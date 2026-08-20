"""Driver: runs the eight worked examples from the assignment plus at least one
malformed request through the same loop. A malformed request is caught and reported
per-request; it never aborts the run (design.md "Phase 5 - Worked-example driver
behavior").
"""
from rlr import RLRRequest, RLRRequestProcessor

WORKED_EXAMPLES = [
    ("Example 1 - interpolated crossing", RLRRequest(
        car_id="car-1",
        stop_line=((5.0, 100.0), (15.0, 100.0)),
        trajectory=[(10, 7, 90), (11, 8, 95), (12, 7, 98), (13, 7, 102)],
    ), 12.5),
    ("Example 2 - never reaches the line", RLRRequest(
        car_id="car-2",
        stop_line=((5.0, 100.0), (15.0, 97.0)),
        trajectory=[(10, 7, 90), (11, 8, 95), (12, 7, 98)],
    ), None),
    ("Example 3 - tilted-line interpolated crossing", RLRRequest(
        car_id="car-3",
        stop_line=((5.0, 100.0), (15.0, 97.0)),
        trajectory=[(10, 7, 90), (11, 8, 95), (12, 7, 98), (13, 7, 102)],
    ), 12.35),
    ("Example 4 - touch-and-stop", RLRRequest(
        car_id="car-4",
        stop_line=((9.0, 97.0), (19.0, 94.0)),
        trajectory=[(10, 7, 90), (11, 8, 95), (12, 9, 97)],
    ), None),
    ("Example 5 - sampled on-line crossing", RLRRequest(
        car_id="car-5",
        stop_line=((5.0, 100.0), (15.0, 100.0)),
        trajectory=[(10, 8, 102), (11, 8, 100), (12, 8, 98)],
    ), 11.0),
    ("Example 6 - crosses infinite line outside segment", RLRRequest(
        car_id="car-6",
        stop_line=((5.0, 100.0), (15.0, 100.0)),
        trajectory=[(10, 20, 102), (11, 20, 98)],
    ), None),
    ("Example 7 - graze and retreat", RLRRequest(
        car_id="car-7",
        stop_line=((5.0, 100.0), (15.0, 100.0)),
        trajectory=[(10, 8, 101.5), (11, 8, 100), (12, 8, 101.5)],
    ), None),
    ("Example 8 - two on-line samples (malformed)", RLRRequest(
        car_id="car-8",
        stop_line=((5.0, 100.0), (15.0, 100.0)),
        trajectory=[(10, 8, 100), (11, 9, 100.5)],
    ), "ValueError"),
]

# An additional, unambiguously malformed request (negative coordinate) demonstrating the
# unhappy path independent of the worked examples' own Example 8.
EXTRA_MALFORMED_REQUEST = ("Malformed request - negative coordinate", RLRRequest(
    car_id="car-9",
    stop_line=((5.0, 100.0), (15.0, 100.0)),
    trajectory=[(10, -1.0, 98.0)],
))


def _run_worked_example(processor, label, request, expected):
    try:
        result = processor.process_request(request)
    except ValueError as exc:
        status = "OK (raised as expected)" if expected == "ValueError" else "MISMATCH"
        print(f"{label}: REJECTED - ValueError: {exc}  [{status}]")
        return
    match = "OK" if _almost_equal(result.crossing_timestamp, expected) else "MISMATCH"
    print(
        f"{label}: crossing_timestamp={result.crossing_timestamp!r} "
        f"(expected={expected!r}) [{match}]"
    )


def _almost_equal(actual, expected):
    if expected is None or actual is None:
        return actual == expected
    return abs(actual - expected) < 1e-6


def main():
    processor = RLRRequestProcessor()

    for label, request, expected in WORKED_EXAMPLES:
        _run_worked_example(processor, label, request, expected)

    label, request = EXTRA_MALFORMED_REQUEST
    try:
        processor.process_request(request)
    except ValueError as exc:
        print(f"{label}: REJECTED - ValueError: {exc}")

    print("\nDriver finished: all requests processed, including the malformed ones.")


if __name__ == "__main__":
    main()
