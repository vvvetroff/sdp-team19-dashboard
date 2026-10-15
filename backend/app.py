import os
import asyncio
from typing import Annotated
from contextlib import asynccontextmanager

import redis
import serial 
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Path, HTTPException

from helpers import println
from websocket_management import ConnectionManager
from background_tasks import BackgroundTasks, BackgroundTasksSerial
from endpoints import RedisOpertations, get_all_ducks_in_dms, get_all_ducks_in_serial

load_dotenv()
REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT: int = int(os.getenv('REDIS_PORT', 6379))
poll_task: asyncio.Task | None = None
manager = ConnectionManager()

# NOTE : uncomment these for demo day
# SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyUSB0')
# SERIAL_BAUDRATE = int(os.getenv('SERIAL_BAUDRATE', 115200))
# ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=1)

@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Lifespan of the server"""

	# startup
	println("Good morning! Starting up server...")
	global redis_client, poll_task
	try:
		redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
		redis_client.ping()
		println(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}...")
	except Exception as e:
		println(f"Failed to connect to Redis: {e}")

    # NOTE : uncomment and comment the other bg_task for demo day
	# bg_task = asyncio.create_task(
	# 	BackgroundTasksSerial(manager=manager, redis_client=redis_client, ser=ser).serial_main()
	# 	)

	bg_task = asyncio.create_task(
		BackgroundTasks(manager=manager, redis_client=redis_client).main()
		)
	println("Background main loop started OK")

	# runtime
	yield

	# shutdown
	if bg_task is not None:
		bg_task.cancel()
		try:
			await bg_task
		except asyncio.CancelledError:
			pass
		bg_task = None
	println("Good night! Shutting down server...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
	allow_credentials=True
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
	"""Websocket endpoint for the dashboard"""
	await manager.connect(websocket)
	try:
		while True:
			await websocket.receive_text()
	except WebSocketDisconnect:
		pass
	finally:
		await manager.disconnect(websocket)

@app.get("/api/health")
async def api_get_health():
	"""Health endpoint for the server"""
	return JSONResponse(content="OK", status_code=200)

@app.get("/api/{device_id}/metrics")
async def api_get_device_metrics(
	device_id: Annotated[str, Path(title="The DuckLink device ID, as shown in the dashboard, e.g. DUCK0001")]
	) -> dict[str, list[str]]:
	"""Gets the metrics for a device"""
	try:
		result = await RedisOpertations(redis_client=redis_client).get_metrics_per_duck(device_id=device_id)
		return result
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/{device_id}/metrics/{metric}")
async def api_get_(
	device_id: Annotated[str, Path(title="The DuckLink device ID, as shown in the dashboard, e.g. DUCK0001")], 
	metric: Annotated[str, Path(title="The desired metric, e.g. voltage")]
	) -> dict[str, list[str]]:
	"""Gets the metric for a device"""
	try:
		result = await RedisOpertations(redis_client=redis_client).get_values_of_metric_per_duck(device_id=device_id, metric=metric)
		return result
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ducks")
async def get_ducks() -> dict[str, list[str]]:
	"""Gets the ducks for the server"""
	try:
		# result = await get_all_ducks_in_serial()
		result = await RedisOpertations(redis_client=redis_client).get_all_ducks()
		return result
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

