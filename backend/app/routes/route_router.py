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
        return crud.create_route(db=db, route=route)
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
    return list(crud.get_routes(db=db, skip=skip, limit=limit))


@router.get("/{route_id}", response_model=schemas.RouteResponse)
def get_route(route_id: RouteId, db: DbSession) -> schemas.RouteResponse:
    route = crud.get_route(db=db, route_id=route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return route


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
    return route


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(route_id: RouteId, db: DbSession) -> Response:
    deleted = crud.delete_route(db=db, route_id=route_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
