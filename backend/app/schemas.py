from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


RouteNumber = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
]
ShortText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
RegistrationNumber = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)
]
BusType = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
]
BusStatus = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=30),
]


class SchemaBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class RouteCreate(SchemaBase):
    route_number: RouteNumber
    name: ShortText
    source: ShortText
    destination: ShortText
    description: str | None = None
    is_active: bool = True


class RouteUpdate(SchemaBase):
    route_number: RouteNumber | None = None
    name: ShortText | None = None
    source: ShortText | None = None
    destination: ShortText | None = None
    description: str | None = None
    is_active: bool | None = None


class RouteResponse(RouteCreate):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime


class BusCreate(SchemaBase):
    registration_number: RegistrationNumber
    route_id: int | None = Field(default=None, gt=0)
    bus_type: BusType
    operator_name: ShortText | None = None
    capacity: int | None = Field(default=None, gt=0)
    status: BusStatus = "inactive"
    is_active: bool = True


class BusUpdate(SchemaBase):
    registration_number: RegistrationNumber | None = None
    route_id: int | None = Field(default=None, gt=0)
    bus_type: BusType | None = None
    operator_name: ShortText | None = None
    capacity: int | None = Field(default=None, gt=0)
    status: BusStatus | None = None
    is_active: bool | None = None


class BusResponse(BusCreate):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime


class BusLocationCreate(SchemaBase):
    bus_id: int = Field(gt=0)
    latitude: Decimal = Field(
        ge=Decimal("-90"),
        le=Decimal("90"),
        max_digits=9,
        decimal_places=6,
    )
    longitude: Decimal = Field(
        ge=Decimal("-180"), le=Decimal("180"), max_digits=9, decimal_places=6
    )
    speed_kmph: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=5,
        decimal_places=2,
    )
    heading_degrees: int | None = Field(default=None, ge=0, le=359)
    recorded_at: datetime


class BusLocationUpdate(SchemaBase):
    latitude: Decimal | None = Field(
        default=None, ge=Decimal("-90"), le=Decimal("90"), max_digits=9, decimal_places=6
    )
    longitude: Decimal | None = Field(
        default=None, ge=Decimal("-180"), le=Decimal("180"), max_digits=9, decimal_places=6
    )
    speed_kmph: Decimal | None = Field(
        default=None, ge=Decimal("0"), max_digits=5, decimal_places=2
    )
    heading_degrees: int | None = Field(default=None, ge=0, le=359)
    recorded_at: datetime | None = None


class BusLocationResponse(BusLocationCreate):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int = Field(gt=0)
    received_at: datetime
