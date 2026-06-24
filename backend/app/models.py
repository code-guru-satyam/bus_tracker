from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (
        UniqueConstraint("route_number", name="uq_routes_route_number"),
        Index("ix_routes_source_destination", "source", "destination"),
        Index("ix_routes_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    destination: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    buses: Mapped[list[Bus]] = relationship(
        back_populates="route",
        cascade="save-update, merge",
    )
    route_stops: Mapped[list["RouteStop"]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RouteStop.sequence_number",
    )


class RouteStop(Base):
    __tablename__ = "route_stops"
    __table_args__ = (
        UniqueConstraint("route_id", "sequence_number", name="uq_route_stops_route_sequence"),
        Index("ix_route_stops_route_id", "route_id"),
        Index("ix_route_stops_sequence_number", "sequence_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    stop_name: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    route: Mapped[Route] = relationship(back_populates="route_stops")


class Bus(Base):
    __tablename__ = "buses"
    __table_args__ = (
        UniqueConstraint("registration_number", name="uq_buses_registration_number"),
        CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_buses_capacity_positive"),
        Index("ix_buses_route_status", "route_id", "status"),
        Index("ix_buses_bus_type", "bus_type"),
        Index("ix_buses_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_number: Mapped[str] = mapped_column(String(40), nullable=False)
    route_id: Mapped[int | None] = mapped_column(
        ForeignKey("routes.id", ondelete="SET NULL"),
        nullable=True,
    )
    bus_type: Mapped[str] = mapped_column(String(50), nullable=False)
    operator_name: Mapped[str | None] = mapped_column(String(120))
    capacity: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="inactive", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    route: Mapped[Route | None] = relationship(back_populates="buses")
    locations: Mapped[list[BusLocation]] = relationship(
        back_populates="bus",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class BusLocation(Base):
    __tablename__ = "bus_locations"
    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_bus_locations_latitude_range",
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_bus_locations_longitude_range",
        ),
        CheckConstraint(
            "speed_kmph IS NULL OR speed_kmph >= 0",
            name="ck_bus_locations_speed_non_negative",
        ),
        CheckConstraint(
            "heading_degrees IS NULL OR "
            "(heading_degrees >= 0 AND heading_degrees <= 359)",
            name="ck_bus_locations_heading_range",
        ),
        Index("ix_bus_locations_bus_recorded_at", "bus_id", "recorded_at"),
        Index("ix_bus_locations_recorded_at", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bus_id: Mapped[int] = mapped_column(
        ForeignKey("buses.id", ondelete="CASCADE"),
        nullable=False,
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    speed_kmph: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    heading_degrees: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    bus: Mapped[Bus] = relationship(back_populates="locations")
