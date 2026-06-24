from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db


router = APIRouter(prefix="/routes", tags=["Routes"])

DbSession = Annotated[Session, Depends(get_db)]
RouteId = Annotated[int, Path(gt=0)]


@router.post(
    "",
    response_model=schemas.RouteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_route(route: schemas.RouteCreate, db: DbSession) -> schemas.RouteResponse:
    try:
        db_route = crud.create_route(db=db, route=route)
        return schemas.RouteResponse.model_validate(crud._build_route_response(db_route))
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Route already exists or violates database constraints.",
        ) from exc


@router.get("", response_model=list[schemas.RouteResponse])
def get_routes(
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[schemas.RouteResponse]:
    routes = crud.get_routes(db=db, skip=skip, limit=limit)
    return [
        schemas.RouteResponse.model_validate(crud._build_route_response(route))
        for route in routes
    ]


@router.get("/{route_id}", response_model=schemas.RouteResponse)
def get_route(route_id: RouteId, db: DbSession) -> schemas.RouteResponse:
    route = crud.get_route(db=db, route_id=route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return schemas.RouteResponse.model_validate(crud._build_route_response(route))


@router.put("/{route_id}", response_model=schemas.RouteResponse)
def update_route(
    route_id: RouteId,
    route_update: schemas.RouteUpdate,
    db: DbSession,
) -> schemas.RouteResponse:
    try:
        route = crud.update_route(db=db, route_id=route_id, route_update=route_update)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Route update violates database constraints.",
        ) from exc

    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return schemas.RouteResponse.model_validate(crud._build_route_response(route))


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(route_id: RouteId, db: DbSession) -> Response:
    deleted = crud.delete_route(db=db, route_id=route_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{route_id}/stops", response_model=list[schemas.RouteStopResponse])
def get_route_stops(route_id: RouteId, db: DbSession) -> list[schemas.RouteStopResponse]:
    if crud.get_route(db=db, route_id=route_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return list(crud.get_route_stops(db=db, route_id=route_id))


@router.post(
    "/{route_id}/stops",
    response_model=schemas.RouteStopResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_route_stop(
    route_id: RouteId,
    route_stop: schemas.RouteStopCreate,
    db: DbSession,
) -> schemas.RouteStopResponse:
    if crud.get_route(db=db, route_id=route_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )

    try:
        return crud.create_route_stop(db=db, route_id=route_id, route_stop=route_stop)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Route stop violates database constraints.",
        ) from exc


StopId = Annotated[int, Path(gt=0)]


@router.put("/{route_id}/stops/{stop_id}", response_model=schemas.RouteStopResponse)
def update_route_stop(
    route_id: RouteId,
    stop_id: StopId,
    route_stop_update: schemas.RouteStopUpdate,
    db: DbSession,
) -> schemas.RouteStopResponse:
    if crud.get_route(db=db, route_id=route_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )

    try:
        route_stop = crud.update_route_stop(
            db=db,
            route_id=route_id,
            stop_id=stop_id,
            route_stop_update=route_stop_update,
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Route stop update violates database constraints.",
        ) from exc

    if route_stop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route stop not found.",
        )
    return route_stop


@router.delete("/{route_id}/stops/{stop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route_stop(route_id: RouteId, stop_id: StopId, db: DbSession) -> Response:
    if crud.get_route(db=db, route_id=route_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )

    deleted = crud.delete_route_stop(db=db, route_id=route_id, stop_id=stop_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route stop not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{route_id}/geometry", response_model=schemas.RouteGeometryResponse)
def get_route_geometry(route_id: RouteId, db: DbSession) -> schemas.RouteGeometryResponse:
    if crud.get_route(db=db, route_id=route_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )

    try:
        coordinates = crud.get_route_geometry(db=db, route_id=route_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return schemas.RouteGeometryResponse(route_id=route_id, coordinates=coordinates)
