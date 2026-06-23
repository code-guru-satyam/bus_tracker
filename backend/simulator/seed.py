from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from urllib.error import HTTPError, URLError

from simulator.common import DEFAULT_API_URL, DEFAULT_TIMEOUT_SECONDS, api_request, build_api_url
from simulator.route_paths import (
    BUS_TYPES,
    DEFAULT_BUSES_PER_ROUTE,
    FLEET_ROUTES,
    OPERATORS,
    SPEED_BY_BUS_TYPE,
    SimulatedRoute,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SeededBus:
    id: int
    registration_number: str
    route_id: int
    route_number: str
    min_speed_kmph: int
    max_speed_kmph: int
    coordinates: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class FleetSeedResult:
    routes_created: int
    buses_created: int
    buses: tuple[SeededBus, ...]


def _parse_json(response_body: str) -> object:
    if not response_body:
        return None
    return json.loads(response_body)


def _fetch_routes(api_url: str, timeout: float) -> list[dict[str, object]]:
    url = build_api_url(api_url, "/api/v1/routes?limit=100")
    try:
        _, response_body = api_request(url, timeout=timeout)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Could not fetch routes from {url}: {exc}") from exc

    payload = _parse_json(response_body)
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected routes response format.")
    return payload


def _fetch_buses(api_url: str, timeout: float) -> list[dict[str, object]]:
    url = build_api_url(api_url, "/api/v1/buses?limit=100&is_active=true")
    try:
        _, response_body = api_request(url, timeout=timeout)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Could not fetch buses from {url}: {exc}") from exc

    payload = _parse_json(response_body)
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected buses response format.")
    return payload


def _create_route(api_url: str, route: SimulatedRoute, timeout: float) -> dict[str, object]:
    url = build_api_url(api_url, "/api/v1/routes")
    payload = {
        "route_number": route.route_number,
        "name": route.name,
        "source": route.source,
        "destination": route.destination,
        "description": route.description,
        "is_active": True,
    }
    try:
        _, response_body = api_request(url, method="POST", payload=payload, timeout=timeout)
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Failed to create route {route.route_number}: {exc.code} {error_body}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach API while creating route {route.route_number}: {exc.reason}") from exc

    created = _parse_json(response_body)
    if not isinstance(created, dict):
        raise RuntimeError(f"Unexpected create-route response for {route.route_number}.")
    return created


def _create_bus(
    api_url: str,
    *,
    registration_number: str,
    route_id: int,
    bus_type: str,
    operator_name: str,
    timeout: float,
) -> dict[str, object]:
    url = build_api_url(api_url, "/api/v1/buses")
    payload = {
        "registration_number": registration_number,
        "route_id": route_id,
        "bus_type": bus_type,
        "operator_name": operator_name,
        "capacity": 52,
        "status": "active",
        "is_active": True,
    }
    try:
        _, response_body = api_request(url, method="POST", payload=payload, timeout=timeout)
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Failed to create bus {registration_number}: {exc.code} {error_body}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not reach API while creating bus {registration_number}: {exc.reason}"
        ) from exc

    created = _parse_json(response_body)
    if not isinstance(created, dict):
        raise RuntimeError(f"Unexpected create-bus response for {registration_number}.")
    return created


def _registration_number(route_number: str, index: int) -> str:
    route_suffix = route_number.replace("-", "")[-4:]
    return f"UP{route_suffix}{index:03d}"


def _route_by_number(routes: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    indexed: dict[str, dict[str, object]] = {}
    for route in routes:
        route_number = route.get("route_number")
        if isinstance(route_number, str):
            indexed[route_number] = route
    return indexed


def _build_seeded_bus(
    bus: dict[str, object],
    route_lookup: dict[int, SimulatedRoute],
    route_number_lookup: dict[int, str],
) -> SeededBus | None:
    bus_id = bus.get("id")
    registration_number = bus.get("registration_number")
    route_id = bus.get("route_id")
    bus_type = bus.get("bus_type")

    if not isinstance(bus_id, int):
        return None
    if not isinstance(registration_number, str):
        return None
    if not isinstance(route_id, int):
        return None
    if not isinstance(bus_type, str):
        bus_type = "ordinary"

    route_number = route_number_lookup.get(route_id)
    simulated_route = route_lookup.get(route_id)
    if route_number is None or simulated_route is None:
        return None

    min_speed, max_speed = SPEED_BY_BUS_TYPE.get(bus_type, (simulated_route.min_speed_kmph, simulated_route.max_speed_kmph))
    return SeededBus(
        id=bus_id,
        registration_number=registration_number,
        route_id=route_id,
        route_number=route_number,
        min_speed_kmph=min_speed,
        max_speed_kmph=max_speed,
        coordinates=tuple(
            (str(latitude), str(longitude)) for latitude, longitude in simulated_route.coordinates
        ),
    )


def load_fleet_buses(
    api_url: str = DEFAULT_API_URL,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[SeededBus, ...]:
    routes = _fetch_routes(api_url, timeout)
    route_number_lookup = {
        route_id: route_number
        for route_number, route in _route_by_number(routes).items()
        for route_id in [route.get("id")]
        if isinstance(route_id, int)
    }
    route_lookup = {
        route_id: simulated_route
        for simulated_route in FLEET_ROUTES
        for route in [_route_by_number(routes).get(simulated_route.route_number)]
        for route_id in [route.get("id") if route is not None else None]
        if isinstance(route_id, int)
    }

    seeded_buses: list[SeededBus] = []
    for bus in _fetch_buses(api_url, timeout):
        seeded = _build_seeded_bus(bus, route_lookup, route_number_lookup)
        if seeded is not None:
            seeded_buses.append(seeded)

    seeded_buses.sort(key=lambda item: item.id)
    return tuple(seeded_buses)


def ensure_fleet_data(
    api_url: str = DEFAULT_API_URL,
    *,
    buses_per_route: int = DEFAULT_BUSES_PER_ROUTE,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> FleetSeedResult:
    if buses_per_route <= 0:
        raise ValueError("buses_per_route must be greater than 0.")

    routes_created = 0
    buses_created = 0

    existing_routes = _fetch_routes(api_url, timeout)
    routes_by_number = _route_by_number(existing_routes)

    for route in FLEET_ROUTES:
        if route.route_number in routes_by_number:
            continue
        created_route = _create_route(api_url, route, timeout)
        routes_by_number[route.route_number] = created_route
        routes_created += 1
        logger.info("Created route %s", route.route_number)

    refreshed_routes = _fetch_routes(api_url, timeout)
    routes_by_number = _route_by_number(refreshed_routes)

    existing_buses = _fetch_buses(api_url, timeout)
    existing_registrations = {
        registration
        for registration in (
            bus.get("registration_number")
            for bus in existing_buses
            if isinstance(bus.get("registration_number"), str)
        )
        if isinstance(registration, str)
    }

    for route in FLEET_ROUTES:
        route_record = routes_by_number.get(route.route_number)
        if route_record is None:
            continue

        route_id = route_record.get("id")
        if not isinstance(route_id, int):
            continue

        for index in range(1, buses_per_route + 1):
            registration_number = _registration_number(route.route_number, index)
            if registration_number in existing_registrations:
                continue

            bus_type = BUS_TYPES[(index - 1) % len(BUS_TYPES)]
            operator_name = OPERATORS[(index - 1) % len(OPERATORS)]
            _create_bus(
                api_url,
                registration_number=registration_number,
                route_id=route_id,
                bus_type=bus_type,
                operator_name=operator_name,
                timeout=timeout,
            )
            existing_registrations.add(registration_number)
            buses_created += 1
            logger.info("Created bus %s on route %s", registration_number, route.route_number)

    seeded_buses = load_fleet_buses(api_url, timeout=timeout)
    logger.info(
        "Fleet seed complete: routes_created=%s buses_created=%s active_buses=%s",
        routes_created,
        buses_created,
        len(seeded_buses),
    )
    return FleetSeedResult(
        routes_created=routes_created,
        buses_created=buses_created,
        buses=seeded_buses,
    )
