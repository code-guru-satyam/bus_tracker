from __future__ import annotations

import argparse
import logging
from decimal import Decimal
from urllib.error import HTTPError, URLError

from simulator.common import (
    DEFAULT_API_URL,
    DEFAULT_BUS_ID,
    DEFAULT_INTERVAL_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    build_location_url,
    build_payload,
    generate_route_points,
    post_location,
)


ROUTE_COORDINATES: tuple[tuple[Decimal, Decimal], ...] = (
    (Decimal("26.799"), Decimal("82.204")),
    (Decimal("26.800"), Decimal("82.205")),
    (Decimal("26.801"), Decimal("82.206")),
    (Decimal("26.802"), Decimal("82.207")),
)

MIN_SPEED_KMPH = 20
MAX_SPEED_KMPH = 60

logger = logging.getLogger("gps_simulator")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate GPS updates for a bus.")
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Base API URL. Defaults to {DEFAULT_API_URL}.",
    )
    parser.add_argument(
        "--bus-id",
        type=int,
        default=DEFAULT_BUS_ID,
        help=f"Bus ID to simulate. Defaults to {DEFAULT_BUS_ID}.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Seconds between updates. Defaults to {DEFAULT_INTERVAL_SECONDS}.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"HTTP request timeout in seconds. Defaults to {DEFAULT_TIMEOUT_SECONDS}.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Send one pass through the simulated route and exit.",
    )
    return parser.parse_args()


def simulate_route(
    api_url: str,
    bus_id: int,
    interval_seconds: float,
    timeout_seconds: float,
    run_once: bool,
) -> None:
    import random
    import time

    if bus_id <= 0:
        raise ValueError("bus_id must be greater than 0.")
    if interval_seconds <= 0:
        raise ValueError("interval must be greater than 0.")
    if timeout_seconds <= 0:
        raise ValueError("timeout must be greater than 0.")

    location_url = build_location_url(api_url)
    logger.info("Sending GPS updates to %s for bus_id=%s", location_url, bus_id)

    max_updates = len(ROUTE_COORDINATES) * 5 if run_once else None
    updates_sent = 0

    try:
        for latitude, longitude, heading_degrees in generate_route_points(ROUTE_COORDINATES):
            speed_kmph = random.randint(MIN_SPEED_KMPH, MAX_SPEED_KMPH)
            payload = build_payload(
                bus_id=bus_id,
                latitude=latitude,
                longitude=longitude,
                speed_kmph=speed_kmph,
                heading_degrees=heading_degrees,
            )
            try:
                status_code, response_body = post_location(
                    url=location_url,
                    payload=payload,
                    timeout=timeout_seconds,
                )
                logger.info(
                    "Location sent lat=%s lon=%s speed=%s heading=%s status=%s response=%s",
                    latitude,
                    longitude,
                    speed_kmph,
                    heading_degrees,
                    status_code,
                    response_body,
                )
            except HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                logger.error(
                    "API rejected location lat=%s lon=%s status=%s response=%s",
                    latitude,
                    longitude,
                    exc.code,
                    error_body,
                )
            except URLError as exc:
                logger.error("Could not reach API at %s: %s", location_url, exc.reason)

            updates_sent += 1
            if max_updates is not None and updates_sent >= max_updates:
                logger.info("Completed one simulated route pass.")
                return

            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("GPS simulator stopped by user.")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    args = parse_args()
    simulate_route(
        api_url=args.api_url,
        bus_id=args.bus_id,
        interval_seconds=args.interval,
        timeout_seconds=args.timeout,
        run_once=args.once,
    )


if __name__ == "__main__":
    main()
