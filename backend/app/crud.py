from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app import models, schemas


def _commit_and_refresh(db: Session, instance: object) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(instance)


def _apply_updates(instance: object, update_data: dict[str, object]) -> None:
    for field, value in update_data.items():
        setattr(instance, field, value)


def create_route(db: Session, route: schemas.RouteCreate) -> models.Route:
    db_route = models.Route(**route.model_dump())
    db.add(db_route)
    _commit_and_refresh(db, db_route)
    return db_route


def get_route(db: Session, route_id: int) -> models.Route | None:
    statement = (
        select(models.Route)
        .options(selectinload(models.Route.route_stops))
        .where(models.Route.id == route_id)
    )
    return db.scalars(statement).first()


def get_routes(db: Session, skip: int = 0, limit: int = 100) -> Sequence[models.Route]:
    statement = (
        select(models.Route)
        .options(selectinload(models.Route.route_stops))
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(statement).all()


def _build_route_response(route: models.Route) -> dict:
    """Convert Route ORM model to response dict with calculated stop_count."""
    return {
        "id": route.id,
        "route_number": route.route_number,
        "name": route.name,
        "source": route.source,
        "destination": route.destination,
        "description": route.description,
        "is_active": route.is_active,
        "stop_count": len(route.route_stops) if route.route_stops else 0,
        "created_at": route.created_at,
        "updated_at": route.updated_at,
    }


def get_route_stops(db: Session, route_id: int) -> Sequence[models.RouteStop]:
    statement = (
        select(models.RouteStop)
        .where(models.RouteStop.route_id == route_id)
        .order_by(models.RouteStop.sequence_number)
    )
    return db.scalars(statement).all()


def get_route_stop(db: Session, route_id: int, stop_id: int) -> models.RouteStop | None:
    statement = (
        select(models.RouteStop)
        .where(models.RouteStop.route_id == route_id)
        .where(models.RouteStop.id == stop_id)
    )
    return db.scalars(statement).first()


def create_route_stop(
    db: Session,
    route_id: int,
    route_stop: schemas.RouteStopCreate,
) -> models.RouteStop:
    if get_route(db=db, route_id=route_id) is None:
        raise ValueError("Route not found")

    db_route_stop = models.RouteStop(route_id=route_id, **route_stop.model_dump())
    db.add(db_route_stop)
    _commit_and_refresh(db, db_route_stop)
    return db_route_stop


def update_route_stop(
    db: Session,
    route_id: int,
    stop_id: int,
    route_stop_update: schemas.RouteStopUpdate,
) -> models.RouteStop | None:
    db_route_stop = get_route_stop(db=db, route_id=route_id, stop_id=stop_id)
    if db_route_stop is None:
        return None

    update_data = route_stop_update.model_dump(exclude_unset=True)
    _apply_updates(db_route_stop, update_data)
    _commit_and_refresh(db, db_route_stop)
    return db_route_stop


def delete_route_stop(db: Session, route_id: int, stop_id: int) -> bool:
    db_route_stop = get_route_stop(db=db, route_id=route_id, stop_id=stop_id)
    if db_route_stop is None:
        return False

    try:
        db.delete(db_route_stop)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return True


def get_route_geometry(db: Session, route_id: int) -> list[list[float]]:
    if get_route(db=db, route_id=route_id) is None:
        raise ValueError("Route not found")

    route_stops = get_route_stops(db=db, route_id=route_id)
    return [[float(stop.latitude), float(stop.longitude)] for stop in route_stops]


def update_route(
    db: Session,
    route_id: int,
    route_update: schemas.RouteUpdate,
) -> models.Route | None:
    db_route = get_route(db, route_id)
    if db_route is None:
        return None

    update_data = route_update.model_dump(exclude_unset=True)
    _apply_updates(db_route, update_data)
    _commit_and_refresh(db, db_route)
    return db_route


def delete_route(db: Session, route_id: int) -> bool:
    db_route = get_route(db, route_id)
    if db_route is None:
        return False

    try:
        db.delete(db_route)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return True


def create_bus(db: Session, bus: schemas.BusCreate) -> models.Bus:
    db_bus = models.Bus(**bus.model_dump())
    db.add(db_bus)
    _commit_and_refresh(db, db_bus)
    return db_bus


def get_bus(db: Session, bus_id: int) -> models.Bus | None:
    return db.get(models.Bus, bus_id)


def get_buses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    route_id: int | None = None,
    is_active: bool | None = None,
) -> Sequence[models.Bus]:
    statement: Select[tuple[models.Bus]] = select(models.Bus)

    if route_id is not None:
        statement = statement.where(models.Bus.route_id == route_id)
    if is_active is not None:
        statement = statement.where(models.Bus.is_active == is_active)

    statement = statement.offset(skip).limit(limit)
    return db.scalars(statement).all()


def update_bus(
    db: Session,
    bus_id: int,
    bus_update: schemas.BusUpdate,
) -> models.Bus | None:
    db_bus = get_bus(db, bus_id)
    if db_bus is None:
        return None

    update_data = bus_update.model_dump(exclude_unset=True)
    _apply_updates(db_bus, update_data)
    _commit_and_refresh(db, db_bus)
    return db_bus


def delete_bus(db: Session, bus_id: int) -> bool:
    db_bus = get_bus(db, bus_id)
    if db_bus is None:
        return False

    try:
        db.delete(db_bus)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return True


def create_bus_location(
    db: Session,
    bus_location: schemas.BusLocationCreate,
) -> models.BusLocation:
    db_bus_location = models.BusLocation(**bus_location.model_dump())
    db.add(db_bus_location)
    _commit_and_refresh(db, db_bus_location)
    return db_bus_location


def get_latest_bus_location(db: Session, bus_id: int) -> models.BusLocation | None:
    statement = (
        select(models.BusLocation)
        .where(models.BusLocation.bus_id == bus_id)
        .order_by(models.BusLocation.recorded_at.desc(), models.BusLocation.id.desc())
        .limit(1)
    )
    return db.scalars(statement).first()


def get_bus_location_history(
    db: Session,
    bus_id: int,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[models.BusLocation]:
    statement = (
        select(models.BusLocation)
        .where(models.BusLocation.bus_id == bus_id)
        .order_by(models.BusLocation.recorded_at.desc(), models.BusLocation.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(statement).all()

