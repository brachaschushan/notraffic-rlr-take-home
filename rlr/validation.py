"""Structural & value validation (design.md: "Validation design").

No geometry here - this layer answers "is this request well-formed," never "did the
vehicle cross." The on-line-count check (which does need geometry) lives in processor.py,
consuming the count produced as a side effect of the single classification pass.
"""
import math


def _is_finite_number(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def validate_car_id(car_id) -> None:
    if not isinstance(car_id, str) or car_id.strip() == "":
        raise ValueError("car_id must be a non-empty, non-whitespace string")


def _validate_point_2d(point, label: str) -> None:
    if point is None or not isinstance(point, (tuple, list)) or len(point) != 2:
        raise ValueError(f"{label} must be a 2-tuple of numeric coordinates")
    x, y = point
    for name, value in (("x", x), ("y", y)):
        if not _is_finite_number(value):
            raise ValueError(f"{label} {name} must be a finite number")
        if value < 0:
            raise ValueError(f"{label} {name} must not be negative")


def validate_stop_line(stop_line) -> None:
    if stop_line is None or not isinstance(stop_line, (tuple, list)) or len(stop_line) != 2:
        raise ValueError("stop_line must be a pair of points")
    a, b = stop_line
    _validate_point_2d(a, "stop_line[0]")
    _validate_point_2d(b, "stop_line[1]")
    if tuple(a) == tuple(b):
        raise ValueError("stop_line endpoints must not be identical")


def validate_trajectory_point(point) -> None:
    if point is None or not isinstance(point, (tuple, list)) or len(point) != 3:
        raise ValueError("trajectory point must be a (t, x, y) triple")
    t, x, y = point
    if not _is_finite_number(t):
        raise ValueError("trajectory point timestamp must be a finite number")
    for name, value in (("x", x), ("y", y)):
        if not _is_finite_number(value):
            raise ValueError(f"trajectory point {name} must be a finite number")
        if value < 0:
            raise ValueError(f"trajectory point {name} must not be negative")
