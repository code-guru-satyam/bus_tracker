from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.websocket.connection_manager import connection_manager


router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/buses/{bus_id}")
async def bus_location_websocket(
    websocket: WebSocket,
    bus_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    if bus_id <= 0 or crud.get_bus(db=db, bus_id=bus_id) is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(bus_id=bus_id, websocket=websocket)

    try:
        latest_location = crud.get_latest_bus_location(db=db, bus_id=bus_id)
        if latest_location is not None:
            payload = schemas.BusLocationResponse.model_validate(latest_location).model_dump(
                mode="json",
            )
            await websocket.send_json({"type": "latest_location", "data": payload})

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await connection_manager.disconnect(bus_id=bus_id, websocket=websocket)
    except RuntimeError:
        await connection_manager.disconnect(bus_id=bus_id, websocket=websocket)
