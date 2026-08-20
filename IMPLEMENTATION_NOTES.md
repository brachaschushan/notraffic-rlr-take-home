# IMPLEMENTATION_NOTES.md

Factual record of this implementation session. Not a second design document - see
`design.md` for the design itself and `critic.md` for the review that shaped it.

## Files changed

- `rlr/models.py` (new) - `RLRRequest`/`RLRResult` dataclasses, exactly per the spec.
- `rlr/geometry.py` (new) - point-to-segment distance, signed side, on-line classification.
- `rlr/validation.py` (new) - structural/value validation (`car_id`, stop-line, trajectory
  points), no geometry.
- `rlr/processor.py` (new) - `find_crossing` (single-pass scan) and `RLRRequestProcessor`
  (public API + exception boundary).
- `rlr/__init__.py` (new) - package exports.
- `tests/__init__.py` (new) - makes `tests/` discoverable by `python -m unittest`.
- `tests/test_rlr_processor.py` (new) - 54 tests across 12 `TestCase` classes.
- `main.py` (new) - worked-example + malformed-request driver.
- `README.md` (new) - install/run instructions, assumptions summary.
- `NOTES.md` (new) - AI-usage disclosure.
- `IMPLEMENTATION_NOTES.md` (new, this file).

No existing file (`context.md`, `plan.md`, `design.md`, `critic.md`, `tests.md`) was
modified.

## Design decisions implemented

- Point-to-segment distance (on-line/segment-membership test) — `rlr/geometry.py:20-27` — `point_to_segment_distance`.
- Signed cross-product (strict-side test, infinite line) — `rlr/geometry.py:30-32` — `signed_cross`/`strict_side`.
- Unified 1px+epsilon tolerance for both raw samples and interpolated crossings (Finding 1) — `rlr/geometry.py:35-37`, `rlr/processor.py:17` — `is_on_line` reused in `_interpolate_crossing`'s membership check.
- Exact-line interpolation parameter driving both space and time (Assumptions A2/A3) — `rlr/processor.py:13-18` — single `alpha` used for the crossing point and the timestamp.
- Single left-to-right scan; on-line count and transition search in one pass (Finding 4, Assumption 1) — `rlr/processor.py:22-90` — `find_crossing`.
- Adjacency lemma / sample-transition vs. interpolation dispatch — `rlr/processor.py:76-85`.
- Vector/cross-product geometry only, no slope-based formula (Finding 6) — `rlr/geometry.py:20-32` (no `x1==x2` branch anywhere).
- Structural/value validation kept separate from geometry — `rlr/validation.py:1-51`.
- Whitespace-only `car_id` rejected (A8) — `rlr/validation.py:11-13`.
- Stop-line identical-endpoints check, exact equality (Finding 5) — `rlr/validation.py:28-29`.
- Timestamp finite/numeric requirement (A5) — `rlr/validation.py:41-42`.
- Total-processor exception boundary — `rlr/processor.py:100-106`.

## Critique fixes implemented

- Objection 1: On-line-count-exceeded fallback — `rlr/processor.py:80-85` (the `else` branch abandons transition tracking once more than one on-line sample sits between the boundaries) — verified by `tests/test_rlr_processor.py::TestSampledOnLineBehavior::test_three_on_line_samples_between_strict_boundaries_raises_value_error`.
- Objection 2: Interleaved single pass (validation + classification in one loop) — `rlr/processor.py:42-46` (`validation.validate_trajectory_point(sample)` called inside `find_crossing`'s own loop, not a separate prior pass) — verified by manual instrumentation (see Verification below), since this is an implementation-shape claim, not a black-box behavioral difference (per `tests.md`).
- Objection 3: Explicit catch-all exception boundary — `rlr/processor.py:101-106` — verified by `tests/test_rlr_processor.py::TestTotality::test_extreme_magnitude_coordinates_do_not_leak_unhandled_exception`.

## Verification

- `python -m unittest` from the repo root: **54 tests, all passing** (0 failures, 0 errors).
- `python main.py`: all 8 worked examples matched their expected values (`[OK]`); both
  deliberately malformed requests (Example 8, and an extra negative-coordinate request)
  were reported as `ValueError` without stopping the run; process exited with code 0.
- Objection 2 manual verification: wrapped the trajectory in a custom list subclass
  counting `__iter__` calls and ran a full request through `RLRRequestProcessor` -
  the trajectory was iterated **exactly once**, confirming validation and classification
  share a single pass rather than two sequential traversals.
- All three `critic.md` objections: fixes implemented and their regression checks pass (two
  via `unittest`, one via the manual instrumentation check above, per `tests.md`'s own
  classification of Objection 2 as non-unittest-representable).
- Assumptions in the code match `context.md`'s decision register (A1-A8, F1, F5-F8); no
  Part 2 behavior (unsorted/duplicate-timestamp handling, multiple crossings, streaming,
  configurable tolerance, multiple/dynamic stop-lines) was introduced.
- Only standard-library imports appear anywhere in `rlr/`, `tests/`, or `main.py`
  (`dataclasses`, `math`, `unittest`) - confirmed by inspection.
