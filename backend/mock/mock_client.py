import asyncio
import json
import websockets

async def connect():
	async with websockets.connect("ws://localhost:8000/ws") as websocket:
		while True:
			message = await websocket.recv()
			json_message = json.loads(message)
			print(json_message)
			await asyncio.sleep(1)

asyncio.run(connect())