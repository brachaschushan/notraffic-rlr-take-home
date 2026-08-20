"""Pure geometry primitives (design.md: "Geometry design").

Two distinct geometric computations are used throughout, and deliberately kept separate:
  - point-to-*segment*-distance decides whether a point is "on-line" (within the 1px
    tolerance), for both raw samples and interpolated crossing points (Finding 1).
  - the signed cross product relative to the *infinite* supporting line decides which
    strict side a (non-on-line) point falls on (Finding 2, confirmed via Example 6).

All formulas are vector/cross-product based, never slope-based, so vertical and horizontal
stop-lines need no special-casing (Finding 6).
"""
import math

Point = tuple[float, float]

TOLERANCE_PX = 1.0
EPSILON = 1e-9  # absorbs floating-point rounding at the exact 1px boundary (Finding 7)


def point_to_segment_distance(a: Point, b: Point, p: Point) -> float:
    """Euclidean distance from p to the finite segment [a, b] (clamped projection)."""
    ab_x, ab_y = b[0] - a[0], b[1] - a[1]
    ap_x, ap_y = p[0] - a[0], p[1] - a[1]
    ab_len_sq = ab_x * ab_x + ab_y * ab_y
    t = (ap_x * ab_x + ap_y * ab_y) / ab_len_sq
    t = max(0.0, min(1.0, t))
    closest_x, closest_y = a[0] + t * ab_x, a[1] + t * ab_y
    return math.hypot(p[0] - closest_x, p[1] - closest_y)


def signed_cross(a: Point, b: Point, p: Point) -> float:
    """Sign encodes which half-plane of the *infinite* line through a,b contains p."""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def is_on_line(a: Point, b: Point, p: Point) -> bool:
    """A point is on-line iff its distance to the finite segment is <=1px (+epsilon)."""
    return point_to_segment_distance(a, b, p) <= TOLERANCE_PX + EPSILON


def strict_side(a: Point, b: Point, p: Point) -> int:
    """+1 or -1 for a point already known not to be on-line."""
    return 1 if signed_cross(a, b, p) > 0 else -1
