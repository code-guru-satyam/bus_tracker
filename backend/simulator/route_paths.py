from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


Coordinate = tuple[Decimal, Decimal]


@dataclass(frozen=True, slots=True)
class SimulatedRoute:
    route_number: str
    name: str
    source: str
    destination: str
    description: str
    coordinates: tuple[Coordinate, ...]
    min_speed_kmph: int
    max_speed_kmph: int


def _coord(latitude: str, longitude: str) -> Coordinate:
    return (Decimal(latitude), Decimal(longitude))


FLEET_ROUTES: tuple[SimulatedRoute, ...] = (
    SimulatedRoute(
        route_number="UP-LKO-01",
        name="Lucknow Charbagh - Gomti Nagar",
        source="Charbagh",
        destination="Gomti Nagar",
        description="East-west corridor across central Lucknow.",
        coordinates=(
            _coord("26.8315", "80.9250"),
            _coord("26.8380", "80.9350"),
            _coord("26.8450", "80.9450"),
            _coord("26.8520", "80.9550"),
            _coord("26.8585", "80.9650"),
            _coord("26.8650", "80.9750"),
        ),
        min_speed_kmph=25,
        max_speed_kmph=45,
    ),
    SimulatedRoute(
        route_number="UP-LKO-02",
        name="Lucknow Hazratganj - Alambagh",
        source="Hazratganj",
        destination="Alambagh",
        description="Southbound city service through Hazratganj and Aminabad.",
        coordinates=(
            _coord("26.8520", "80.9440"),
            _coord("26.8460", "80.9380"),
            _coord("26.8400", "80.9320"),
            _coord("26.8340", "80.9260"),
            _coord("26.8280", "80.9200"),
            _coord("26.8220", "80.9140"),
        ),
        min_speed_kmph=20,
        max_speed_kmph=40,
    ),
    SimulatedRoute(
        route_number="UP-KNP-01",
        name="Kanpur Civil Lines - Kanpur Central",
        source="Civil Lines",
        destination="Kanpur Central",
        description="North-south corridor linking Civil Lines to Kanpur Central.",
        coordinates=(
            _coord("26.4720", "80.3310"),
            _coord("26.4650", "80.3380"),
            _coord("26.4580", "80.3450"),
            _coord("26.4510", "80.3520"),
            _coord("26.4440", "80.3590"),
            _coord("26.4370", "80.3660"),
        ),
        min_speed_kmph=30,
        max_speed_kmph=50,
    ),
    SimulatedRoute(
        route_number="UP-VNS-01",
        name="Varanasi Godaulia - BHU",
        source="Godaulia",
        destination="Banaras Hindu University",
        description="Heritage city route from Godaulia to BHU campus.",
        coordinates=(
            _coord("25.3100", "82.9850"),
            _coord("25.3050", "82.9900"),
            _coord("25.3000", "82.9950"),
            _coord("25.2950", "83.0000"),
            _coord("25.2900", "83.0050"),
            _coord("25.2850", "83.0100"),
        ),
        min_speed_kmph=18,
        max_speed_kmph=38,
    ),
    SimulatedRoute(
        route_number="UP-AGR-01",
        name="Agra Taj - Agra Cantt",
        source="Taj Mahal",
        destination="Agra Cantt",
        description="Tourist corridor from Taj Mahal area to Agra Cantt station.",
        coordinates=(
            _coord("27.1750", "78.0420"),
            _coord("27.1700", "78.0300"),
            _coord("27.1650", "78.0180"),
            _coord("27.1600", "78.0060"),
            _coord("27.1550", "77.9940"),
            _coord("27.1500", "77.9820"),
        ),
        min_speed_kmph=22,
        max_speed_kmph=42,
    ),
    SimulatedRoute(
        route_number="UP-PYJ-01",
        name="Prayagraj Civil Lines - Sangam",
        source="Civil Lines",
        destination="Sangam",
        description="Prayagraj route from Civil Lines toward the Sangam ghats.",
        coordinates=(
            _coord("25.4350", "81.8460"),
            _coord("25.4300", "81.8400"),
            _coord("25.4250", "81.8340"),
            _coord("25.4200", "81.8280"),
            _coord("25.4150", "81.8220"),
            _coord("25.4100", "81.8160"),
        ),
        min_speed_kmph=24,
        max_speed_kmph=44,
    ),
)

BUS_TYPES: tuple[str, ...] = ("ordinary", "AC", "deluxe")
OPERATORS: tuple[str, ...] = ("UPSRTC", "UPSRTC", "Private Express", "City Connect")

SPEED_BY_BUS_TYPE: dict[str, tuple[int, int]] = {
    "ordinary": (22, 42),
    "AC": (32, 52),
    "deluxe": (38, 62),
}

DEFAULT_BUSES_PER_ROUTE = 4
