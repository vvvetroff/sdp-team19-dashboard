import asyncio
import json
from typing import Any
from fastapi import WebSocket

class ConnectionManager:
	"""Keeps active WebSocket clients and broadcasts JSON to all of them."""

	def __init__(self) -> None:
		self._connections: list[WebSocket] = []
		self._lock = asyncio.Lock()

	async def connect(self, websocket: WebSocket) -> None:
		await websocket.accept()
		async with self._lock:
			self._connections.append(websocket)

	async def disconnect(self, websocket: WebSocket) -> None:
		async with self._lock:
			self._connections.remove(websocket)

	async def broadcast_json(self, payload: dict[str, Any]) -> None:
		text = json.dumps(payload)
		async with self._lock:
			if not self._connections:
				return
			snapshot = self._connections
		dead: list[WebSocket] = []
		for ws in snapshot:
			try:
				await ws.send_text(text)
			except Exception:
				dead.append(ws)
		if dead:
			async with self._lock:
				for ws in dead:
					self._connections.remove(ws)
