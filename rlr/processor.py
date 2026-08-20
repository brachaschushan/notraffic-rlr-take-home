from . import validation
from .geometry import EPSILON, TOLERANCE_PX, is_on_line, point_to_segment_distance, signed_cross, strict_side
from .models import RLRRequest, RLRResult


def _interpolate_crossing(a, b, p1, p2):
    """p1, p2 are (t, x, y) samples on strictly opposite sides. Returns the crossing
    timestamp if the spatial crossing point lies within the finite-segment tolerance
    (Finding 1), else None (Example 6: crosses the infinite line outside the segment).
    """
    t1, x1, y1 = p1
    t2, x2, y2 = p2
    c1 = signed_cross(a, b, (x1, y1))
    c2 = signed_cross(a, b, (x2, y2))
    alpha = c1 / (c1 - c2)  # in (0, 1): c1, c2 have opposite signs by construction
    cross_point = (x1 + alpha * (x2 - x1), y1 + alpha * (y2 - y1))
    if point_to_segment_distance(a, b, cross_point) <= TOLERANCE_PX + EPSILON:
        return t1 + alpha * (t2 - t1)
    return None


def find_crossing(stop_line, trajectory):
    """Single left-to-right pass (design.md: "Phase 3", "State and invariants").

    Returns (crossing_timestamp: float | None, on_line_count: int). Never raises -
    this layer stays validation-free; the caller decides what an on_line_count > 1
    means. Safe (never crashes) for any on_line_count, per the on-line-count-exceeded
    fallback that closes critic.md Objection 1.
    """
    a, b = stop_line

    first_side = None
    prev_strict_sample = None
    pending_on_line = []  # on-line samples seen since prev_strict_sample, not yet resolved

    transition_found = False
    fallback_triggered = False
    crossing_timestamp = None

    on_line_count = 0

    for sample in trajectory:
        # Structural/value validation is interleaved into this same loop iteration,
        # immediately before classification of the same point (critic.md Objection 2:
        # one pass, not a separate prior traversal).
        validation.validate_trajectory_point(sample)
        t, x, y = sample
        p = (x, y)

        if is_on_line(a, b, p):
            on_line_count += 1
            if on_line_count > 1:
                fallback_triggered = True
            if not fallback_triggered and not transition_found:
                pending_on_line.append(sample)
            continue

        if fallback_triggered or transition_found:
            continue

        side = strict_side(a, b, p)

        if first_side is None:
            first_side = side
            prev_strict_sample = sample
            pending_on_line = []
            continue

        if side == first_side:
            prev_strict_sample = sample
            pending_on_line = []
            continue

        # side differs from first_side: this is the one guaranteed transition.
        transition_found = True
        if len(pending_on_line) == 0:
            crossing_timestamp = _interpolate_crossing(a, b, prev_strict_sample, sample)
        elif len(pending_on_line) == 1:
            crossing_timestamp = pending_on_line[0][0]
        else:
            # More than one on-line sample between the boundaries: only reachable for
            # malformed input (on_line_count already > 1 here too). Abandon transition
            # tracking entirely and defer to the caller's on-line-count check.
            fallback_triggered = True
            crossing_timestamp = None

    if fallback_triggered:
        crossing_timestamp = None

    return crossing_timestamp, on_line_count


class RLRRequestProcessor:
    def process_request(self, request: RLRRequest) -> RLRResult:
        # Total-processor exception boundary (design.md "Error-handling design"; the
        # concrete mechanism added per critic.md Objection 3): every ValueError raised
        # below propagates as-is; anything else unexpected is converted to ValueError
        # rather than escaping. Finding 8's accepted residual risk (extreme-magnitude
        # coordinates producing numerically meaningless results) still stands - this
        # only guarantees no *other* exception type ever leaks out.
        try:
            return self._process(request)
        except ValueError:
            raise
        except Exception as exc:  # pragma: no cover - defensive catch-all boundary
            raise ValueError(f"malformed request: {exc}") from exc

    def _process(self, request: RLRRequest) -> RLRResult:
        validation.validate_car_id(request.car_id)
        validation.validate_stop_line(request.stop_line)

        if len(request.trajectory) < 2:
            for sample in request.trajectory:
                validation.validate_trajectory_point(sample)
            return RLRResult(car_id=request.car_id, crossing_timestamp=None)

        crossing_timestamp, on_line_count = find_crossing(request.stop_line, request.trajectory)
        if on_line_count > 1:
            raise ValueError("more than one trajectory sample lies on the stop-line")
        return RLRResult(car_id=request.car_id, crossing_timestamp=crossing_timestamp)
