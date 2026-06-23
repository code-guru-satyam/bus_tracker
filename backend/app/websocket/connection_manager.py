from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Iterable

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState


logger = logging.getLogger(__name__)


class BusConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, bus_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[bus_id].add(websocket)
        logger.info("WebSocket client connected for bus_id=%s", bus_id)

    async def disconnect(self, bus_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(bus_id)
            if connections is None:
                return

            connections.discard(websocket)
            if not connections:
                self._connections.pop(bus_id, None)
        logger.info("WebSocket client disconnected for bus_id=%s", bus_id)

    async def broadcast_to_bus(self, bus_id: int, message: dict[str, object]) -> None:
        connections = await self._get_connections(bus_id)
        if not connections:
            return

        stale_connections: list[WebSocket] = []
        for websocket in connections:
            try:
                if websocket.client_state != WebSocketState.CONNECTED:
                    stale_connections.append(websocket)
                    continue
                await websocket.send_json(message)
            except (RuntimeError, WebSocketDisconnect):
                stale_connections.append(websocket)

        for websocket in stale_connections:
            await self.disconnect(bus_id=bus_id, websocket=websocket)

    async def connection_count(self, bus_id: int) -> int:
        return len(await self._get_connections(bus_id))

    async def _get_connections(self, bus_id: int) -> Iterable[WebSocket]:
        async with self._lock:
            return tuple(self._connections.get(bus_id, set()))


connection_manager = BusConnectionManager()
