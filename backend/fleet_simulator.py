from __future__ import annotations

import argparse
import logging
import random
import signal
import threading
import time
from decimal import Decimal
from urllib.error import HTTPError, URLError

from simulator.common import (
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT_SECONDS,
    build_location_url,
    build_payload,
    generate_route_points,
    post_location,
)
from simulator.route_paths import DEFAULT_BUSES_PER_ROUTE
from simulator.seed import FleetSeedResult, SeededBus, ensure_fleet_data, load_fleet_buses


DEFAULT_INTERVAL_SECONDS = 5.0
DEFAULT_MIN_BUSES = 20
SHUTDOWN_POLL_SECONDS = 0.5
SHUTDOWN_JOIN_TIMEOUT_SECONDS = 15.0

logger = logging.getLogger("fleet_simulator")
stop_event = threading.Event()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulate GPS updates for a fleet of buses concurrently.",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Base API URL. Defaults to {DEFAULT_API_URL}.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Base seconds between updates per bus. Defaults to {DEFAULT_INTERVAL_SECONDS}.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"HTTP request timeout in seconds. Defaults to {DEFAULT_TIMEOUT_SECONDS}.",
    )
    parser.add_argument(
        "--buses-per-route",
        type=int,
        default=DEFAULT_BUSES_PER_ROUTE,
        help=f"Buses to seed per route when seeding. Defaults to {DEFAULT_BUSES_PER_ROUTE}.",
    )
    parser.add_argument(
        "--min-buses",
        type=int,
        default=DEFAULT_MIN_BUSES,
        help=f"Minimum active buses required before simulation starts. Defaults to {DEFAULT_MIN_BUSES}.",
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Seed fleet routes and buses, then exit without simulating.",
    )
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Skip seeding and simulate only buses already present in the API.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Send one pass through each bus route and exit.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Run for this many seconds, then stop automatically.",
    )
    return parser.parse_args()


def _coordinates_for_bus(bus: SeededBus) -> tuple[tuple[Decimal, Decimal], ...]:
    return tuple((Decimal(latitude), Decimal(longitude)) for latitude, longitude in bus.coordinates)


def _interval_for_bus(base_interval: float, bus_id: int) -> float:
    jitter = random.uniform(-0.8, 0.8)
    return max(2.0, base_interval + jitter + ((bus_id % 5) * 0.15))


def _request_shutdown(reason: str) -> None:
    if stop_event.is_set():
        logger.warning("Forced exit.")
        raise SystemExit(1)

    logger.info("%s Shutting down fleet simulator...", reason)
    stop_event.set()


def _handle_shutdown_signal(signum: int, _frame: object | None) -> None:
    _request_shutdown(f"Stop requested (signal {signum}).")


def _wait_or_stop(seconds: float) -> bool:
    return stop_event.wait(seconds)


def _join_threads(threads: list[threading.Thread], timeout: float) -> list[str]:
    deadline = time.monotonic() + timeout
    for thread in threads:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        thread.join(timeout=remaining)

    return [thread.name for thread in threads if thread.is_alive()]


def simulate_bus(
    *,
    api_url: str,
    bus: SeededBus,
    interval_seconds: float,
    timeout_seconds: float,
    run_once: bool,
) -> None:
    location_url = build_location_url(api_url)
    route_coordinates = _coordinates_for_bus(bus)
    start_segment = bus.id % len(route_coordinates)
    start_step = bus.id % 5
    bus_interval = _interval_for_bus(interval_seconds, bus.id)

    logger.info(
        "Starting bus_id=%s registration=%s route=%s interval=%.2fs speed=%s-%s km/h",
        bus.id,
        bus.registration_number,
        bus.route_number,
        bus_interval,
        bus.min_speed_kmph,
        bus.max_speed_kmph,
    )

    if _wait_or_stop(random.uniform(0, bus_interval)):
        logger.info("bus_id=%s stopped before first update.", bus.id)
        return

    max_updates = len(route_coordinates) * 5 if run_once else None
    updates_sent = 0

    try:
        for latitude, longitude, heading_degrees in generate_route_points(
            route_coordinates,
            start_index=start_segment,
            start_step=start_step,
        ):
            if stop_event.is_set():
                return

            speed_kmph = random.randint(bus.min_speed_kmph, bus.max_speed_kmph)
            payload = build_payload(
                bus_id=bus.id,
                latitude=latitude,
                longitude=longitude,
                speed_kmph=speed_kmph,
                heading_degrees=heading_degrees,
            )
            try:
                status_code, _response_body = post_location(
                    url=location_url,
                    payload=payload,
                    timeout=timeout_seconds,
                )
                logger.info(
                    "bus_id=%s lat=%s lon=%s speed=%s heading=%s status=%s",
                    bus.id,
                    latitude,
                    longitude,
                    speed_kmph,
                    heading_degrees,
                    status_code,
                )
            except HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                logger.error(
                    "bus_id=%s API rejected location status=%s response=%s",
                    bus.id,
                    exc.code,
                    error_body,
                )
            except URLError as exc:
                logger.error("bus_id=%s could not reach API: %s", bus.id, exc.reason)
                return

            updates_sent += 1
            if max_updates is not None and updates_sent >= max_updates:
                logger.info("bus_id=%s completed one simulated route pass.", bus.id)
                return

            if _wait_or_stop(bus_interval):
                logger.info("bus_id=%s stopped.", bus.id)
                return
    except Exception:
        logger.exception("bus_id=%s simulator thread failed.", bus.id)
    finally:
        logger.debug("bus_id=%s simulator thread exited.", bus.id)


def run_fleet_simulation(
    *,
    api_url: str,
    buses: tuple[SeededBus, ...],
    interval_seconds: float,
    timeout_seconds: float,
    run_once: bool,
    duration_seconds: float | None = None,
) -> None:
    if interval_seconds <= 0:
        raise ValueError("interval must be greater than 0.")
    if timeout_seconds <= 0:
        raise ValueError("timeout must be greater than 0.")
    if not buses:
        raise ValueError("At least one bus is required to run the fleet simulator.")

    stop_event.clear()
    signal.signal(signal.SIGINT, _handle_shutdown_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_shutdown_signal)

    location_url = build_location_url(api_url)
    logger.info(
        "Launching fleet simulation for %s buses at %s (press Ctrl+C to stop)",
        len(buses),
        location_url,
    )

    threads: list[threading.Thread] = []
    for bus in buses:
        thread = threading.Thread(
            target=simulate_bus,
            name=f"bus-sim-{bus.id}",
            kwargs={
                "api_url": api_url,
                "bus": bus,
                "interval_seconds": interval_seconds,
                "timeout_seconds": timeout_seconds,
                "run_once": run_once,
            },
            daemon=True,
        )
        threads.append(thread)
        thread.start()

    try:
        deadline = (
            time.monotonic() + duration_seconds
            if duration_seconds is not None and duration_seconds > 0
            else None
        )
        while any(thread.is_alive() for thread in threads):
            if stop_event.is_set():
                break
            if deadline is not None and time.monotonic() >= deadline:
                _request_shutdown(
                    f"Duration limit reached ({duration_seconds:.0f}s)."
                )
                break

            for thread in threads:
                if not thread.is_alive():
                    continue
                thread.join(timeout=SHUTDOWN_POLL_SECONDS)
                if stop_event.is_set():
                    break
    except KeyboardInterrupt:
        _request_shutdown("Stop requested (Ctrl+C).")

    if stop_event.is_set():
        alive_threads = _join_threads(threads, SHUTDOWN_JOIN_TIMEOUT_SECONDS)
        if alive_threads:
            logger.warning(
                "Some simulator threads did not stop within %.0fs: %s",
                SHUTDOWN_JOIN_TIMEOUT_SECONDS,
                ", ".join(alive_threads),
            )
        else:
            logger.info("Fleet simulator stopped.")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    args = parse_args()

    if args.no_seed:
        buses = load_fleet_buses(args.api_url, timeout=args.timeout)
        seed_result = FleetSeedResult(
            routes_created=0,
            buses_created=0,
            buses=buses,
        )
    else:
        seed_result = ensure_fleet_data(
            args.api_url,
            buses_per_route=args.buses_per_route,
            timeout=args.timeout,
        )

    if len(seed_result.buses) < args.min_buses:
        raise SystemExit(
            f"Only {len(seed_result.buses)} simulatable buses found; need at least {args.min_buses}. "
            "Run without --no-seed to create fleet data."
        )

    logger.info(
        "Fleet ready: routes_created=%s buses_created=%s simulatable_buses=%s",
        seed_result.routes_created,
        seed_result.buses_created,
        len(seed_result.buses),
    )

    if args.seed_only:
        return

    run_fleet_simulation(
        api_url=args.api_url,
        buses=seed_result.buses,
        interval_seconds=args.interval,
        timeout_seconds=args.timeout,
        run_once=args.once,
        duration_seconds=args.duration,
    )


if __name__ == "__main__":
    main()
