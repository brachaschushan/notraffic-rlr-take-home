# tests.md — Test Plan for the NoTraffic RLR Assignment

> Role: test designer. This is a **test plan**, not test code. Source precedence: (1) the
> assignment specification, (2) `context.md`, (3) `design.md`, (4) `critic.md`, (5) `plan.md` for
> sequencing/paths. Nothing in this document modifies `context.md`, `plan.md`, `design.md`,
> `critic.md`, or any source/test/driver/README/NOTES file.

**Note on `critic.md` status.** All three objections in `critic.md` were already accepted and
implemented in `design.md` in the prior revision (the on-line-count-exceeded fallback for
Objection 1, the interleaved single-pass pipeline for Objection 2, and the explicit catch-all
exception boundary for Objection 3). No proposed change from `critic.md` remains unaccepted, so
**no test case in this plan is marked `PENDING DESIGN DECISION`** — every expected outcome below
is derived from a decision that is final as of the current `design.md`. If that changes (e.g. a
future critique is only partially accepted), this document's format supports marking individual
cases `PENDING DESIGN DECISION` at that time.

---

## 1. Worked examples from the assignment

`test_example_1_interpolated_crossing_returns_12_5` — Stop-line `(5,100)-(15,100)`; trajectory
`(10,7,90),(11,8,95),(12,7,98),(13,7,102)` → `RLRResult(crossing_timestamp≈12.5)` — Proves:
interpolated crossing on a horizontal line (Interpolation design; Assumptions A2/A3).

`test_example_2_never_reaches_line_returns_none` — Stop-line `(5,100)-(15,97)`; trajectory
`(10,7,90),(11,8,95),(12,7,98)` → `RLRResult(crossing_timestamp=None)` — Proves: no-crossing
contract when the trajectory stays on one strict side (crossing definition condition 1).

`test_example_3_tilted_line_interpolated_crossing_returns_12_35` — Stop-line `(5,100)-(15,97)`
(tilted); trajectory `(10,7,90),(11,8,95),(12,7,98),(13,7,102)` →
`RLRResult(crossing_timestamp≈12.35)` — Proves: interpolation math is orientation-agnostic
(Geometry design: tilted stop-lines).

`test_example_4_touch_and_stop_returns_none` — Stop-line `(9,97)-(19,94)`; trajectory
`(10,7,90),(11,8,95),(12,9,97)` (ends exactly on endpoint A) → `RLRResult(crossing_timestamp=None)`
— Proves: reaching the line without proceeding to the far side is not a crossing.

`test_example_5_sampled_on_line_crossing_returns_11_0` — Stop-line `(5,100)-(15,100)`; trajectory
`(10,8,102),(11,8,100),(12,8,98)` (`t=11` on-line, distance 0) →
`RLRResult(crossing_timestamp=11.0)` — Proves: sample-transition rule — no interpolation when the
transition itself lands on an on-line sample.

`test_example_6_crosses_infinite_line_outside_segment_returns_none` — Stop-line `(5,100)-(15,100)`;
trajectory `(10,20,102),(11,20,98)` → `RLRResult(crossing_timestamp=None)` — Proves: finite-segment
membership check rejects an infinite-line crossing that falls outside the segment (Geometry
design; Finding 1's boundary).

`test_example_7_graze_and_retreat_returns_none` — Stop-line `(5,100)-(15,100)`; trajectory
`(10,8,101.5),(11,8,100),(12,8,101.5)` (`t=11` on-line, both neighbors the same strict side) →
`RLRResult(crossing_timestamp=None)` — Proves: an on-line sample surrounded by the same strict
side is not a crossing (crossing definition condition 1).

`test_example_8_two_on_line_samples_raises_value_error` — Stop-line `(5,100)-(15,100)`; trajectory
`(10,8,100),(11,9,100.5)` (distances 0 and 0.5, both ≤1px) → raises `ValueError` — Proves: the
more-than-one-on-line-sample malformed-input rule.

---

## 2. Basic valid crossings

`test_vertical_stopline_interpolated_crossing` — Stop-line `(10,5)-(10,15)` (vertical); trajectory
with two samples straddling `x=10` on opposite strict sides, no on-line sample between them →
`RLRResult` with a correctly interpolated `crossing_timestamp` — Proves: vertical stop-lines must
be supported (spec, explicit; Finding 6).

`test_vertical_stopline_sampled_on_line_crossing` — Stop-line `(10,5)-(10,15)`; trajectory with the
transition sample itself on-line (`x≈10`, within 1px, `y` inside `[5,15]`) →
`RLRResult(crossing_timestamp=<that sample's t>)` — Proves: sample-transition rule holds
identically for vertical lines.

`test_crossing_from_positive_to_negative_side` — Trajectory transitions from the "+" side to the
"−" side (relative to a fixed stop-line) → correct crossing timestamp — Proves: crossing detection
is not direction-dependent.

`test_crossing_from_negative_to_positive_side` — Same stop-line, trajectory transitions "−" → "+"
→ correct crossing timestamp — Proves: symmetric to the previous case; side labels are arbitrary,
not semantically ordered.

`test_crossing_exactly_at_first_endpoint` — Two straddling samples positioned so the interpolated
crossing point coincides exactly with stop-line endpoint A (distance 0) → `RLRResult` with a valid
interpolated timestamp — Proves: endpoint inclusion under Finding 1's uniform tolerance.

`test_crossing_exactly_at_second_endpoint` — Same, crossing point coincides exactly with endpoint B
→ valid interpolated timestamp — Proves: endpoint inclusion, symmetric case.

`test_crossing_with_integer_valued_coordinates_and_timestamps` — Stop-line, trajectory
coordinates, and timestamps all supplied as Python `int` rather than `float` → `RLRResult` with a
correct (possibly non-integer) `crossing_timestamp` — Proves: normal numeric-type handling (A7 —
no extra structural-type policing beyond what's required).

`test_crossing_with_floating_point_coordinates` — Same scenario with genuinely fractional
coordinates/timestamps throughout → correct interpolated `crossing_timestamp` — Proves: baseline
floating-point correctness independent of the integer case above.

---

## 3. No-crossing behavior

`test_empty_trajectory_returns_none` — `trajectory=[]` → `RLRResult(crossing_timestamp=None)` —
Proves: empty-trajectory contract.

`test_single_point_trajectory_returns_none` — Trajectory has exactly one point, strictly on one
side → `RLRResult(None)` — Proves: a single point can never establish a transition.

`test_single_point_trajectory_on_line_returns_none` — The one point is itself on-line (distance 0)
→ `RLRResult(None)`, **not** `ValueError` — Proves: the single-point rule overrides on-line status;
distinguishes this from the multiple-on-line-samples rule, which requires more than one point to
even apply.

`test_entirely_one_strict_side_returns_none` — All points strictly on the same side, none on-line
→ `RLRResult(None)` — Proves: crossing definition condition 1 (both strict sides must be visited).

`test_approaches_but_never_reaches_line_generalized_returns_none` — A constructed case with a
different stop-line shape than Example 2, trajectory approaching but never entering the tolerance
band → `RLRResult(None)` — Proves: Example 2's rule generalizes beyond its specific geometry.

`test_ends_on_line_without_reaching_far_side_generalized_returns_none` — A constructed case with a
different stop-line shape than Example 4, trajectory ending on-line without a prior or subsequent
opposite-side sample → `RLRResult(None)` — Proves: Example 4's rule generalizes.

`test_starts_on_line_then_stays_one_side_returns_none` — First sample on-line, all subsequent
samples the same strict side → `RLRResult(None)` — Proves: starting on-line does not itself create
a crossing; condition 1 still requires both strict sides.

`test_crosses_infinite_extension_of_tilted_line_outside_segment_returns_none` — A tilted stop-line
(not horizontal, unlike Example 6) with a trajectory crossing its infinite extension well beyond an
endpoint → `RLRResult(None)` — Proves: Example 6's rule generalizes to non-horizontal lines.

`test_near_segment_but_no_side_change_returns_none` — Multiple points close to the segment (a mix
of on-line and one strict side only) but both strict sides are never visited → `RLRResult(None)` —
Proves: proximity to the line does not by itself imply a crossing; condition 1 is about sides
visited, not distance.

---

## 4. One-pixel tolerance boundaries

`test_sampled_point_distance_zero_is_on_line` — A sample exactly on the segment (distance 0),
positioned as the transition sample → classified on-line; contributes to the on-line count and,
as the sole on-line sample at the transition, drives the sample-transition rule — Proves: on-line
definition inclusivity at distance 0.

`test_sampled_point_distance_less_than_one_is_on_line` — A sample at ~0.5px from the segment
interior, positioned as the transition sample → on-line, sample-transition rule applies — Proves:
≤1px on-line rule, interior case.

`test_sampled_point_distance_exactly_one_is_on_line` — A sample at exactly 1.0px from the segment
interior → classified on-line (inclusive `≤`) — Proves: the spec's "one pixel or less" is
inclusive at the boundary, and Finding 7's epsilon does not accidentally exclude the exact
boundary.

`test_sampled_point_distance_just_over_one_is_strict_side` — A sample at 1.01px from the segment
interior (well beyond Finding 7's ~1e-9 epsilon) → classified strictly on one side, not on-line —
Proves: the tolerance is bounded, not open-ended; Finding 7's epsilon absorbs floating-point noise
without meaningfully widening the geometric contract.

`test_sampled_point_near_endpoint_within_capsule_is_on_line` — A sample within 1px of an endpoint
but beyond the segment's straight corridor (in the capsule's rounded cap) → on-line — Proves: the
capsule-shaped tolerance near endpoints (Geometry design: "points near endpoints").

`test_sampled_point_near_endpoint_just_outside_capsule_is_strict_side` — A sample just over 1px
from the nearest endpoint, beyond the rounded cap → classified strictly on one side — Proves: the
capsule tolerance is bounded even near endpoints, not an indefinite corridor extension.

`test_interpolation_targets_exact_line_not_tolerance_band_edge` — Two straddling samples chosen so
that interpolating to the edge of the ±1px tolerance band (an incorrect implementation) would
produce a different spatial crossing point than interpolating to the exact mathematical supporting
line (the correct implementation) → assert the result matches the exact-line computation, not the
band-edge computation — Proves: Assumptions A2/A3 (interpolation targets the exact line; the
tolerance only classifies sampled points, it does not redefine the interpolation target).

---

## 5. Finite-segment versus infinite-line behavior

`test_interpolated_crossing_clearly_inside_segment` — Crossing point well within `[A, B]`, away
from both endpoints → valid crossing — Proves: baseline finite-segment membership.

`test_interpolated_crossing_exactly_at_endpoint_a` — Crossing point coincides exactly with A
(distance 0) → valid crossing — Proves: Finding 1's endpoint inclusion.

`test_interpolated_crossing_exactly_at_endpoint_b` — Crossing point coincides exactly with B →
valid crossing — Proves: Finding 1's endpoint inclusion, symmetric case.

`test_interpolated_crossing_slightly_before_first_endpoint` — Crossing point ~0.5px before A along
the line's extension (within the capsule) → valid crossing — Proves: Finding 1's capsule tolerance
extends up to 1px before A, reversing the original stricter Assumption 4.

`test_interpolated_crossing_slightly_beyond_second_endpoint` — Crossing point ~0.5px beyond B
(within the capsule) — the exact scenario `context.md`'s Finding 1 discussion used as its running
example (`(15.5, 100)` vs. endpoint `(15, 100)`) → valid crossing — Proves: Finding 1's resolution
directly, using its own worked scenario.

`test_interpolated_crossing_well_outside_segment_returns_none` — Crossing point ~5px beyond an
endpoint (Example 6's pattern, restated generically) → `RLRResult(None)` — Proves: the tolerance
does not extend indefinitely.

`test_interpolated_crossing_just_beyond_capsule_tolerance_returns_none` — Crossing point at
endpoint-distance 1.01px (just past the capsule) → `RLRResult(None)` — Proves: the exact boundary
of Finding 1's extended tolerance, distinguishing "valid because within 1px" from "invalid because
barely beyond."

---

## 6. Sampled on-line behavior

`test_side_a_on_line_side_b_sample_transition` — Sequence `[strict A, on-line, strict B]` →
crossing at the on-line sample's own timestamp — Proves: sample-transition rule, generalized
beyond Example 5's specific geometry.

`test_side_a_on_line_side_a_no_crossing` — Sequence `[strict A, on-line, strict A]` →
`RLRResult(None)` — Proves: graze pattern, generalized beyond Example 7.

`test_on_line_first_point_then_one_side_returns_none` — Sequence `[on-line, strict A, strict A]` →
`RLRResult(None)` — Proves: a leading on-line sample alone does not establish a crossing.

`test_on_line_last_point_after_one_side_returns_none` — Sequence `[strict A, strict A, on-line]` →
`RLRResult(None)` — Proves: a trailing on-line sample alone does not establish a crossing (mirrors
Example 4's ending-on-line pattern).

`test_one_on_line_point_off_transition_no_crossing_returns_none` — Sequence
`[strict A, strict A, on-line, strict A]` (the on-line sample is a blip, not at a real
transition) → `RLRResult(None)`; on-line count is exactly 1, so no `ValueError` — Proves: an
off-transition on-line sample does not manufacture a crossing, and does not itself violate the
on-line-count rule.

`test_two_on_line_samples_raises_value_error` — (Example 8; cross-referenced here for category
completeness.)

`test_more_than_two_on_line_samples_raises_value_error` — Four or more on-line samples anywhere in
the trajectory → `ValueError` — Proves: the on-line-count rule applies to any count beyond one, not
just exactly two.

`test_three_on_line_samples_between_strict_boundaries_raises_value_error` — The exact scenario
`critic.md` Objection 1 uses: `[strict A, on-line, on-line, on-line, strict B]` → `ValueError`,
with no crash and no other exception type — Proves: `design.md`'s "State and invariants"
on-line-count-exceeded fallback; **this is the regression test for `critic.md` Objection 1** (see
§15).

---

## 7. Stop-line validation

`test_stopline_identical_endpoints_raises_value_error` — `A == B` exactly (bit-for-bit) →
`ValueError` — Proves: Finding 5's must-raise rule.

`test_stopline_negative_x_raises_value_error` — `A=(-1, 5)` → `ValueError` — Proves:
negative-coordinate rule.

`test_stopline_negative_y_raises_value_error` — `A=(5, -1)` → `ValueError` — Proves:
negative-coordinate rule, y-axis case.

`test_stopline_nonnumeric_coordinate_raises_value_error` — `A=("five", 5)` → `ValueError`, not
`TypeError` — Proves: totality + non-numeric rejection.

`test_stopline_nan_coordinate_raises_value_error` — `A=(float('nan'), 5)` → `ValueError` — Proves:
NaN rejection (A5's numeric-validity extension applied to stop-line coordinates).

`test_stopline_positive_infinity_coordinate_raises_value_error` — `A=(float('inf'), 5)` →
`ValueError` — Proves: infinite-coordinate rejection.

`test_stopline_negative_infinity_coordinate_raises_value_error` — `A=(float('-inf'), 5)` →
`ValueError` — Proves: infinite-coordinate rejection, negative case.

`test_stopline_malformed_point_arity_raises_value_error` — `A=(5, 5, 5)` (3-tuple) → `ValueError`
— Proves: structural-malformation rule for stop-line points.

`test_stopline_none_point_raises_value_error` — `stop_line=(None, (5, 5))` → `ValueError`, not
`TypeError`/`AttributeError` — Proves: totality under a structurally malformed stop-line point.

`test_vertical_stopline_is_accepted` — `A=(10, 5), B=(10, 15)` with an otherwise well-formed
request → normal `RLRResult`, no error — Proves: vertical stop-lines are explicitly supported, not
rejected.

`test_zero_valued_coordinates_are_valid` — `A=(0, 0), B=(10, 0)` → normal processing, no error —
Proves: zero is non-negative and must be accepted, not confused with "missing."

`test_very_short_nondegenerate_stopline_is_valid` — `A` and `B` differ by a tiny but non-zero
amount (e.g. `1e-6` apart, not exactly identical) → normal processing, **no** `ValueError` —
Proves: Finding 5's decision that only *exact* identical points are rejected, not near-duplicates
(a case `critic.md`'s "Hidden tests I would expect" specifically calls out).

---

## 8. Trajectory validation

`test_trajectory_negative_x_raises_value_error` — A trajectory point with a negative x coordinate
→ `ValueError`.

`test_trajectory_negative_y_raises_value_error` — A trajectory point with a negative y coordinate
→ `ValueError`.

`test_trajectory_nonnumeric_coordinate_raises_value_error` — A trajectory point with a non-numeric
x or y (e.g. a string) → `ValueError`, not `TypeError`.

`test_trajectory_nan_coordinate_raises_value_error` — A trajectory point with `float('nan')` as x
or y → `ValueError`.

`test_trajectory_infinite_coordinate_raises_value_error` — A trajectory point with `float('inf')`
(and, separately, `float('-inf')`) as x or y → `ValueError`.

`test_trajectory_malformed_sample_arity_raises_value_error` — A trajectory point with 2 or 4
elements instead of 3 → `ValueError`, not a Python unpacking `TypeError`/`ValueError`-from-CPython.

`test_trajectory_none_sample_raises_value_error` — A trajectory element that is `None` itself
(not a 3-tuple) → `ValueError`, not `TypeError`/`AttributeError`.

`test_trajectory_none_coordinate_raises_value_error` — A trajectory point like `(10, None, 90)` →
`ValueError`.

`test_trajectory_two_on_line_points_raises_value_error` — (Example 8; cross-referenced here for
category completeness.)

`test_trajectory_nonnumeric_timestamp_raises_value_error` — `t="ten"` → `ValueError` — Proves: A5,
the timestamp extension of the numeric-validity rule.

`test_trajectory_nan_timestamp_raises_value_error` — `t=float('nan')` → `ValueError` — Proves: A5.

`test_trajectory_positive_infinity_timestamp_raises_value_error` — `t=float('inf')` →
`ValueError` — Proves: A5.

`test_trajectory_negative_infinity_timestamp_raises_value_error` — `t=float('-inf')` →
`ValueError` — Proves: A5.

---

## 9. `car_id` validation

`test_car_id_normal_string_is_valid` — `car_id="car-42"` with an otherwise well-formed request →
normal processing, `result.car_id == "car-42"` — Proves: baseline `car_id` acceptance.

`test_car_id_empty_string_raises_value_error` — `car_id=""` → `ValueError`.

`test_car_id_whitespace_only_raises_value_error` — `car_id="   "` → `ValueError` — Proves: A8
(whitespace-only treated as empty).

`test_car_id_non_string_raises_value_error` — `car_id=123` (an `int`) → `ValueError`.

---

## 10. Totality / exception containment

`test_malformed_point_does_not_leak_type_error` — A structurally malformed trajectory point that
would, under a naive implementation, cause an unpacking or type error → assert only `ValueError`
is observed (via `assertRaises(ValueError)`; any other exception type fails the test as an error,
not merely a failure).

`test_none_stopline_point_does_not_leak_attribute_error` — `stop_line=(None, (5, 5))` (as in §7) →
`ValueError` only, confirmed specifically under the totality framing (no `AttributeError` from
attempting to index into `None`).

`test_malformed_arity_does_not_leak_index_error` — A trajectory point with the wrong number of
elements → `ValueError` only, no `IndexError` from out-of-range unpacking.

`test_extreme_magnitude_coordinates_do_not_leak_unhandled_exception` — `critic.md` Objection 3's
scenario: `A=(0, 0)`, `B=(1e200, 1e200)`, trajectory with similarly extreme-magnitude coordinates
→ `ValueError` or a valid `RLRResult` only — never `AssertionError`, `OverflowError`, or any other
exception type — Proves: the catch-all exception boundary in `design.md`'s Error-handling design;
**this is the regression test for `critic.md` Objection 3** (see §15).

---

## 11. Floating-point and geometry robustness

`test_value_exactly_on_one_pixel_threshold` — (§4's exact-1.0px case, restated here under the
floating-point framing: chosen so a naive `sqrt`-based distance computation without Finding 7's
epsilon could plausibly compute `1.0000000000002` and misclassify it.)

`test_value_just_inside_and_just_outside_threshold_from_both_sides` — Two closely paired cases,
one at `1.0 - 1e-7` (on-line) and one at `1.0 + 1e-7` (strict side), both well outside Finding 7's
~`1e-9` epsilon window — Proves: the epsilon absorbs representation noise without meaningfully
shifting the classification boundary in either direction.

`test_interpolated_crossing_extremely_close_to_endpoint` — Crossing point at endpoint-distance
`0.0001px`, deep within the capsule — Proves: the interpolation formula remains numerically stable
extremely close to an endpoint, not just comfortably inside the segment.

`test_nearly_vertical_stopline_interpolated_crossing` — Stop-line with a very small but non-zero
`dx` (e.g. `B - A = (1e-6, 10)`) → correct crossing, no slope-based blowup — Proves: Finding 6's
vector-based geometry avoids the instability a `dy/dx` formulation would hit near-vertical.

`test_nearly_horizontal_stopline_interpolated_crossing` — Stop-line with a very small but non-zero
`dy` → correct crossing — Proves: symmetric robustness for near-horizontal lines.

`test_very_short_valid_segment_interpolated_crossing` — A short but non-degenerate segment (e.g.
length ~`0.01px`, endpoints still distinct per Finding 5) → correct classification, no
division-by-near-zero blowup in the interpolation `alpha` formula — Proves: `alpha`'s
cross-product ratio is scale-invariant (Interpolation design's derivation — the segment-length
factor cancels algebraically).

`test_large_finite_coordinate_values_produce_valueerror_or_valid_result` — Cross-referenced to
§10's `test_extreme_magnitude_coordinates_do_not_leak_unhandled_exception` (`critic.md`
Objection 3); listed here under the floating-point framing for completeness.

`test_interpolated_timestamp_very_close_to_an_existing_sample_timestamp` — A case constructed so
the true interpolated crossing time is extremely close to (but distinct from) one of the two
straddling samples' own timestamps → the interpolated value, not a value that has collapsed/
rounded onto the neighboring sample's timestamp — Proves: interpolation precision is independent
of how close the true crossing time is to an existing sample.

**Not expressible as a deterministic unit test:** `critic.md` Objection 2 (single interleaved pass
vs. two sequential stages) is an implementation-shape claim — a correct 1-pass and a correct
2-pass implementation are behaviorally indistinguishable from the outside (same `RLRResult`/
`ValueError` for every input). See §15 for the appropriate non-unittest verification (code review
plus an optional iteration-count instrumentation check).

---

## 12. Performance and large-input behavior

`test_large_valid_trajectory_100000_points_processes_successfully` — A synthetic ~100,000-point
trajectory with one clean crossing → correct `RLRResult` — **Category:** normal `unittest`
(functional correctness on a large input; runtime observed informally, not asserted).

`test_large_trajectory_malformed_sample_near_end_raises_value_error` — A ~100,000-point trajectory
whose only malformed sample (e.g. a negative coordinate) is the very last point → `ValueError` —
**Category:** normal `unittest` — Proves: full-trajectory validation is not short-circuited by an
early crossing-looking pattern (Assumption 1).

`test_large_trajectory_second_on_line_sample_near_end_raises_value_error` — A ~100,000-point
trajectory with one on-line sample early on (looking like a valid, complete crossing) and a
second on-line sample near the very end → `ValueError` — **Category:** normal `unittest` — Proves:
the on-line-count check scans the *entire* trajectory and is not fooled by an early plausible
crossing (Assumption 1; directly related to `critic.md` Objection 1's "the loop must continue"
requirement).

`test_large_trajectory_does_not_use_unbounded_extra_storage` — **Category:** manual complexity
review, not a `unittest` case — memory usage is not reliably assertable from a black-box unit
test; verify by code inspection that no per-point classification list or other O(n) auxiliary
structure is built, consistent with "Extra-space complexity: O(1)" in `design.md`.

---

## 13. `RLRResult` behavior

`test_result_car_id_matches_request` — Any valid request → `result.car_id == request.car_id` —
Proves: `RLRResult`'s `car_id` field is a faithful echo of the request, not derived or altered.

`test_valid_crossing_returns_expected_numeric_timestamp` — Generic result-shape check
(complementing the worked-example tests): a valid crossing produces a `float`
`crossing_timestamp`, never `None`, never a non-numeric type.

`test_no_crossing_returns_crossing_timestamp_none` — Generic result-shape check: a non-crossing
request produces `crossing_timestamp=None` exactly (not `0`, not `False`, not omitted).

`test_malformed_request_raises_rather_than_returning_partial_result` — Any must-raise input →
`ValueError` is raised; no `RLRResult` object (partially populated or otherwise) is ever returned
— Proves: totality means strictly "either/or," never a half-valid result.

---

## 14. `main.py` driver behavior

Per `design.md` Phase 5, the driver's verification method is **manual execution**, not `unittest`
— `main.py` has no importable return-value API to assert against as currently designed. These
items are planned verifications, not `unittest.TestCase` methods:

`driver_processes_all_eight_worked_examples` — Run `python main.py` → printed output for all 8
worked examples matches the spec's expected values — Proves: Phase 5 success criteria —
**Verification method:** manual execution.

`driver_includes_at_least_one_malformed_request` — Run `python main.py` → the fixed request list
includes at least one deliberately malformed request — Proves: the spec's explicit requirement
that `main.py` "must also demonstrate the unhappy path" — **Verification method:** manual
execution / code review of the request list.

`driver_catches_malformed_request_per_request` — Run `python main.py` → the malformed request's
`ValueError` is caught and reported, never propagates as an uncaught traceback — Proves: Phase 5's
per-request `try/except ValueError` structure — **Verification method:** manual execution (observe
no traceback, no non-zero exit from a crash).

`driver_continues_after_malformed_request` — Run `python main.py` → requests listed after the
malformed one are still processed and printed — Proves: the spec's explicit "a single bad request
must never abort the run" — **Verification method:** manual execution, confirm output includes
results for every request after the malformed one.

**Optional future refinement (not currently part of `design.md`):** if `main.py` is later
refactored to expose a testable helper (e.g. a `run(requests) -> list[str]` function instead of
printing directly), the four items above could become `unittest` cases using
`contextlib.redirect_stdout`/`io.StringIO` or direct return-value assertions. This is not proposed
as a required change here — it is noted only so the option is visible if the driver's design is
revisited.

---

## 15. Critique regression tests

**Critique reference:** Objection 1 (High) — Phase 3's boundary logic was undefined for more than
one on-line sample between the strict-side boundary points.
**Regression test:** `test_three_on_line_samples_between_strict_boundaries_raises_value_error`
(§6). Under the pre-fix design this input's outcome was unspecified (a literal two-case dispatch
implementation could crash or hit an undefined branch); under the fixed design (the on-line-
count-exceeded fallback in "State and invariants") it must complete and raise `ValueError`.

**Critique reference:** Objection 2 (Medium) — `design.md` claimed a single pass while Phase 4's
own pipeline described two sequential stages.
**Regression test:** this is an architecture/performance claim, not an observable functional
difference — a correct 1-pass and a correct 2-pass implementation produce identical
`RLRResult`/`ValueError` outputs for every input, so no black-box `unittest` assertion can
distinguish them. Appropriate verification instead: (a) code review confirming validation and
geometric classification occur within one loop over the trajectory, per the fixed Phase 4 design;
and, optionally, (b) an instrumentation-based check — wrapping the trajectory in a custom iterable
that counts how many times it is iterated, and asserting the count is exactly one — a legitimate
stdlib-only `unittest` technique, but one that tests implementation shape rather than pure
input/output behavior, so it is listed here rather than in the main case inventory above.

**Critique reference:** Objection 3 (Critical) — `design.md` asserted totality as an outcome
without specifying the mechanism that would hold under Finding 8's accepted numeric-overflow risk.
**Regression test:** `test_extreme_magnitude_coordinates_do_not_leak_unhandled_exception` (§10).
Under the pre-fix design this input could plausibly leak `AssertionError`, `OverflowError`, or a
similar internal exception from geometry; under the fixed design (the explicit catch-all boundary
in "Error-handling design") it must produce only `ValueError` or a valid result.

---

## 16. Possible Part 2 tests — do not implement now

All items below are **OUT OF SCOPE FOR PART 1** and must not accidentally become Part 1
requirements:

- **OUT OF SCOPE FOR PART 1** — unsorted timestamps (would require validating or handling
  violations of the ascending-order guarantee currently relied upon per A6).
- **OUT OF SCOPE FOR PART 1** — duplicate timestamps (same guarantee, uniqueness half).
- **OUT OF SCOPE FOR PART 1** — multiple crossings within a single trajectory (would require
  removing the "changes at most once" guarantee, per F3).
- **OUT OF SCOPE FOR PART 1** — multiple side changes generally (same guarantee as above; the
  single-boundary assumption in "State and invariants" would need to be replaced).
- **OUT OF SCOPE FOR PART 1** — streaming/partial trajectory input (would require the on-line-count
  validation to work incrementally rather than over a complete, pre-collected trajectory).
- **OUT OF SCOPE FOR PART 1** — changed/configurable tolerance (would require the `1px`/epsilon
  constants to become parameters instead of fixed values).

---

# unittest structure

**File path (per `plan.md` Step 3):** `tests/test_rlr_processor.py`, runnable from the repository
root via `python -m unittest`. No `pytest` or third-party dependency is used anywhere in this
plan.

**Test classes** (one module, several `TestCase` classes grouped by concern — not one flat class):

- `TestWorkedExamples` — §1. Each of the 8 examples is an individually named test method, per the
  stated rationale: when one fails, the failing example number must be immediately visible in the
  test output, not buried inside a parametrized loop.
- `TestValidCrossings` — §2 (basic valid crossings: vertical/tilted/horizontal, integer/float
  input, endpoint-exact crossings).
- `TestNoCrossing` — §3.
- `TestToleranceBoundaries` — §4.
- `TestFiniteSegmentVsInfiniteLine` — §5.
- `TestSampledOnLineBehavior` — §6, including the two critique-driven cases
  (`test_more_than_two_on_line_samples_raises_value_error`,
  `test_three_on_line_samples_between_strict_boundaries_raises_value_error`).
- `TestStopLineValidation` — §7.
- `TestTrajectoryValidation` — §8.
- `TestCarIdValidation` — §9.
- `TestTotality` — §10, including `test_extreme_magnitude_coordinates_do_not_leak_unhandled_exception`.
- `TestFloatingPointRobustness` — §11.
- `TestLargeTrajectories` — §12 (excluding the manual-complexity-review item, which is not a test
  method at all).
- `TestRLRResultShape` — §13.

**Objection-driven tests are not placed in a separate class.** They live inside their natural
category class (`TestSampledOnLineBehavior`, `TestTotality`) and are named/commented to make the
`critic.md` linkage traceable in the test output itself. §15 above is a cross-reference index, not
a separate implementation location — this avoids duplicate test definitions covering the same
input twice under different names.

**`main.py` driver behavior (§14) is intentionally not part of this `unittest` module**, per
`design.md`'s own stated verification method for Phase 5 (manual execution). If that changes (see
§14's "optional future refinement"), a separate `TestDriver` class could be added later; it is not
proposed here.

**`setUp()` usage:** limited value across most classes, since each test's input is distinct and
purpose-built. The one place `setUp()` (or a small module-level helper function) earns its keep is
a shared `RLRRequest`-construction helper (to avoid repeating the same field names across dozens
of test methods) and a shared `assertTimestampAlmostEqual(actual, expected)` helper wrapping
`assertAlmostEqual` with a precision consistent with Finding 7's epsilon philosophy.

**`subTest` usage:** appropriate specifically for the repetitive malformed-input batteries where
the expected outcome is identical across many structurally similar inputs — e.g. `TestStopLineValidation`'s and
`TestTrajectoryValidation`'s negative/NaN/Infinity/non-numeric variations, and
`TestCarIdValidation`'s empty/whitespace/non-string variations — implemented as one test method
iterating a list of `(description, malformed_request_factory)` pairs under
`with self.subTest(description=...)`. **Individually named tests are preferable** for: all 8
worked examples (distinct expected values, need individual pass/fail visibility); the geometric
edge-case tests in §2, §4, §5, §6, §11 (each proves a materially different geometric rule, and
collapsing them into a loop would obscure which specific geometric claim failed); and both
critique-regression tests in §15 (their individual pass/fail status *is* the signal that
`critic.md`'s fixes hold — bundling them into a generic malformed-input loop would bury that
signal).

**Floating-point timestamp comparison:** `assertAlmostEqual` (or the `setUp()`-provided wrapper
above), never exact `==`, for every `crossing_timestamp` assertion — required because interpolated
results (e.g. `12.35`) involve floating-point division.

**Asserting `ValueError`:** `with self.assertRaises(ValueError): ...` for every must-raise case.
This implicitly also enforces the robustness/totality requirement: if the implementation leaks a
different exception type (e.g. `TypeError`), `assertRaises(ValueError)` does not catch it, and
`unittest` reports the test as an **ERROR** (uncaught exception) rather than a **FAILURE**
(assertion mismatch) — a useful, automatic diagnostic distinction between "wrong `ValueError`
message/absence" and "totality violated by a leaked exception type."

**Capturing stdout for `main.py`:** not required under the current plan (§14 is manual execution),
but if adopted later, `contextlib.redirect_stdout` with `io.StringIO` is the stdlib-only mechanism
consistent with the assignment's standard-library-only constraint.

**Discovery:** `python -m unittest` run from the repository root performs test discovery starting
in the current directory with the default `test*.py` pattern, which matches
`tests/test_rlr_processor.py` directly; an `__init__.py` inside `tests/` is not required for
discovery but may be added for clarity — a minor scaffolding choice, not a testing-strategy
decision.

---

# Requirements-to-tests traceability

| Requirement / design rule | Representative test(s) | Covered? |
|---|---|---|
| Crossing semantics (both strict sides + finite-segment transition) | `test_example_1_...`, `test_example_6_...`, `test_entirely_one_strict_side_returns_none` | Yes |
| 1-pixel tolerance (sampled points) | `test_sampled_point_distance_exactly_one_is_on_line`, `test_sampled_point_distance_just_over_one_is_strict_side` | Yes |
| Sampled (non-interpolated) crossing | `test_example_5_...`, `test_side_a_on_line_side_b_sample_transition` | Yes |
| Interpolated crossing | `test_example_1_...`, `test_example_3_...` | Yes |
| Finite segment / endpoint capsule (Finding 1) | `test_interpolated_crossing_exactly_at_endpoint_a/b`, `test_interpolated_crossing_slightly_beyond_second_endpoint`, `test_interpolated_crossing_well_outside_segment_returns_none` | Yes |
| Graze / no crossing | `test_example_7_...`, `test_side_a_on_line_side_a_no_crossing` | Yes |
| Malformed requests (`ValueError` contract) | §7, §8, §9 in full | Yes |
| Multiple on-line points | `test_example_8_...`, `test_more_than_two_on_line_samples_raises_value_error`, `test_three_on_line_samples_between_strict_boundaries_raises_value_error` | Yes |
| Vertical lines | `test_vertical_stopline_is_accepted`, `test_vertical_stopline_interpolated_crossing`, `test_vertical_stopline_sampled_on_line_crossing` | Yes |
| Totality (`ValueError` or valid result only) | §10 in full, `test_extreme_magnitude_coordinates_do_not_leak_unhandled_exception` | Yes |
| Large trajectories (≤100,000 points) | §12 in full | Yes |
| Driver continuation after malformed input | `driver_continues_after_malformed_request` | **Covered, but not by `unittest`** — see flag below |

**Flag:** "driver continuation after malformed input" is a spec-explicit requirement, and it is
covered by this plan — but only via manual execution (§14), consistent with `design.md`'s stated
Phase 5 verification method, not via `python -m unittest`. Anyone treating a clean `unittest` run
as proof that Phase 5 is satisfied would be mistaken; `main.py` must also be run and its output
read by hand (or the "optional future refinement" in §14 adopted) before Phase 5 can be considered
verified.

---

# Test-plan readiness

- Are all 8 worked examples represented? **Yes** — §1, one individually named test per example.
- Are all explicit `ValueError` cases represented? **Yes** — §7, §8, §9 cover every must-raise
  condition enumerated in `design.md` §2 and the spec.
- Are all accepted assumptions represented where testable? **Yes** — A1 (large-trajectory
  late-malformed-sample tests, §12), A2/A3 (`test_interpolation_targets_exact_line_...`, §4), A4→F1
  (§5's endpoint-capsule tests), A5 (§8's timestamp NaN/Infinity/non-numeric tests), A7 (§2's
  integer-vs-float test), A8 (§9's whitespace test), F5 (§7's very-short-nondegenerate test), F6
  (§11's nearly-vertical/horizontal tests), F7 (§4's exact-1px test), F8 (§10/§11's
  extreme-magnitude test). A6 and F3 are correctly *not* tested per Part 1's scope — recorded in
  §16 instead.
- Are the three critique objections covered? **Yes** — §15 maps each to a concrete regression
  test or, for Objection 2, an explicit non-`unittest` verification method.
- Are tolerance boundaries covered? **Yes** — §4 in full.
- Are segment endpoints covered? **Yes** — §5 in full.
- Is totality covered? **Yes** — §10 in full, plus the Objection 3 regression test.
- Is large-input behavior covered? **Yes** — §12 in full.
- Are Part 2 cases clearly separated? **Yes** — §16, every item explicitly marked
  **OUT OF SCOPE FOR PART 1**.
- Can this test plan be implemented using only `unittest` and the Python standard library? **Yes**
  — every case uses `unittest.TestCase`, `subTest`, `assertRaises`, `assertAlmostEqual`, and at
  most `contextlib`/`io` for the optional, not-currently-adopted stdout-capture refinement; no
  third-party dependency appears anywhere in this plan.

No item above is `No` or `Needs design decision`. This test plan is ready to be translated into
`tests/test_rlr_processor.py` per `plan.md`'s Phase 2/Step 3.
