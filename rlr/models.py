from dataclasses import dataclass


@dataclass(frozen=True)
class RLRRequest:
    car_id: str
    stop_line: tuple[tuple[float, float], tuple[float, float]]
    trajectory: list[tuple[float, float, float]]  # (t, x, y)


@dataclass(frozen=True)
class RLRResult:
    car_id: str
    crossing_timestamp: float | None
