from __future__ import annotations

import json
import math
import random
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_API_URL = "http://127.0.0.1:8000"
DEFAULT_BUS_ID = 1
DEFAULT_INTERVAL_SECONDS = 5.0
DEFAULT_TIMEOUT_SECONDS = 10.0
MOVEMENT_STEPS_PER_SEGMENT = 5
GPS_JITTER = Decimal("0.000030")


def build_api_url(api_url: str, path: str) -> str:
    return f"{api_url.rstrip('/')}{path}"


def build_location_url(api_url: str) -> str:
    return build_api_url(api_url, "/api/v1/locations")


def quantize_coordinate(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"))


def random_coordinate_jitter() -> Decimal:
    return Decimal(str(random.uniform(float(-GPS_JITTER), float(GPS_JITTER))))


def compute_heading(
    start_latitude: Decimal,
    start_longitude: Decimal,
    end_latitude: Decimal,
    end_longitude: Decimal,
) -> int:
    lat1 = math.radians(float(start_latitude))
    lat2 = math.radians(float(end_latitude))
    delta_longitude = math.radians(float(end_longitude - start_longitude))

    x = math.sin(delta_longitude) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        delta_longitude
    )
    bearing = math.degrees(math.atan2(x, y))
    return int((bearing + 360) % 360)


def generate_route_points(
    route_coordinates: tuple[tuple[Decimal, Decimal], ...],
    *,
    start_index: int = 0,
    start_step: int = 0,
) -> Iterator[tuple[Decimal, Decimal, int]]:
    if len(route_coordinates) < 2:
        raise ValueError("route_coordinates must contain at least two points.")

    point_count = len(route_coordinates)
    segment_index = start_index % point_count
    step_index = start_step % MOVEMENT_STEPS_PER_SEGMENT

    while True:
        start = route_coordinates[segment_index]
        end = route_coordinates[(segment_index + 1) % point_count]
        start_latitude, start_longitude = start
        end_latitude, end_longitude = end
        heading_degrees = compute_heading(
            start_latitude,
            start_longitude,
            end_latitude,
            end_longitude,
        )

        for step in range(step_index, MOVEMENT_STEPS_PER_SEGMENT):
            progress = Decimal(step) / Decimal(MOVEMENT_STEPS_PER_SEGMENT)
            latitude = start_latitude + ((end_latitude - start_latitude) * progress)
            longitude = start_longitude + ((end_longitude - start_longitude) * progress)

            yield (
                quantize_coordinate(latitude + random_coordinate_jitter()),
                quantize_coordinate(longitude + random_coordinate_jitter()),
                heading_degrees,
            )

        segment_index = (segment_index + 1) % point_count
        step_index = 0


def build_payload(
    bus_id: int,
    latitude: Decimal,
    longitude: Decimal,
    speed_kmph: int,
    heading_degrees: int,
) -> dict[str, Any]:
    return {
        "bus_id": bus_id,
        "latitude": str(latitude),
        "longitude": str(longitude),
        "speed_kmph": str(speed_kmph),
        "heading_degrees": heading_degrees,
        "recorded_at": datetime.now(UTC).isoformat(),
    }


def api_request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[int, str]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=body, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
        return response.status, response_body


def post_location(
    url: str,
    payload: dict[str, Any],
    timeout: float,
) -> tuple[int, str]:
    return api_request(url, method="POST", payload=payload, timeout=timeout)
