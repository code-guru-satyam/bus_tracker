from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db


router = APIRouter(prefix="/buses", tags=["Buses"])

DbSession = Annotated[Session, Depends(get_db)]
BusId = Annotated[int, Path(gt=0)]


@router.post(
    "",
    response_model=schemas.BusResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bus(bus: schemas.BusCreate, db: DbSession) -> schemas.BusResponse:
    try:
        return crud.create_bus(db=db, bus=bus)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bus already exists or violates database constraints.",
        ) from exc


@router.get("", response_model=list[schemas.BusResponse])
def get_buses(
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    route_id: Annotated[int | None, Query(gt=0)] = None,
    is_active: bool | None = None,
) -> list[schemas.BusResponse]:
    return list(
        crud.get_buses(
            db=db,
            skip=skip,
            limit=limit,
            route_id=route_id,
            is_active=is_active,
        )
    )


@router.get("/{bus_id}", response_model=schemas.BusResponse)
def get_bus(bus_id: BusId, db: DbSession) -> schemas.BusResponse:
    bus = crud.get_bus(db=db, bus_id=bus_id)
    if bus is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found.",
        )
    return bus


@router.put("/{bus_id}", response_model=schemas.BusResponse)
def update_bus(
    bus_id: BusId,
    bus_update: schemas.BusUpdate,
    db: DbSession,
) -> schemas.BusResponse:
    try:
        bus = crud.update_bus(db=db, bus_id=bus_id, bus_update=bus_update)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bus update violates database constraints.",
        ) from exc

    if bus is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found.",
        )
    return bus


@router.delete("/{bus_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bus(bus_id: BusId, db: DbSession) -> Response:
    deleted = crud.delete_bus(db=db, bus_id=bus_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

