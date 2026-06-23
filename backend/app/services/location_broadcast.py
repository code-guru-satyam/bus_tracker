from __future__ import annotations

from app import schemas
from app.websocket.connection_manager import connection_manager


async def broadcast_latest_location(location: schemas.BusLocationResponse) -> None:
    payload = location.model_dump(
        mode="json",
    )
    await connection_manager.broadcast_to_bus(
        bus_id=location.bus_id,
        message={
            "type": "location_update",
            "data": payload,
        },
    )
