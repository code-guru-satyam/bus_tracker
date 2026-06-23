from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.services.location_broadcast import broadcast_latest_location


router = APIRouter(tags=["Locations"])

DbSession = Annotated[Session, Depends(get_db)]
BusId = Annotated[int, Path(gt=0)]


@router.post(
    "/locations",
    response_model=schemas.BusLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bus_location(
    bus_location: schemas.BusLocationCreate,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> schemas.BusLocationResponse:
    if crud.get_bus(db=db, bus_id=bus_location.bus_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found.",
        )

    try:
        location = crud.create_bus_location(db=db, bus_location=bus_location)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bus location violates database constraints.",
        ) from exc

    location_response = schemas.BusLocationResponse.model_validate(location)
    background_tasks.add_task(broadcast_latest_location, location_response)
    return location


@router.get(
    "/buses/{bus_id}/latest-location",
    response_model=schemas.BusLocationResponse,
)
def get_latest_bus_location(
    bus_id: BusId,
    db: DbSession,
) -> schemas.BusLocationResponse:
    if crud.get_bus(db=db, bus_id=bus_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found.",
        )

    location = crud.get_latest_bus_location(db=db, bus_id=bus_id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus location not found.",
        )
    return location


@router.get(
    "/buses/{bus_id}/location-history",
    response_model=list[schemas.BusLocationResponse],
)
def get_bus_location_history(
    bus_id: BusId,
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[schemas.BusLocationResponse]:
    if crud.get_bus(db=db, bus_id=bus_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found.",
        )

    return list(
        crud.get_bus_location_history(
            db=db,
            bus_id=bus_id,
            skip=skip,
            limit=limit,
        )
    )
