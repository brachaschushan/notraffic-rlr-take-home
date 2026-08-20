# NOTES.md - AI Usage

## Tools used

**Claude Code** was used for the entire exercise: requirements analysis, design,
self-critique, test planning, and implementation, run as a sequence of explicit phases
(recorded in `context.md`, `plan.md`, `design.md`, `critic.md`, `tests.md`, culminating in
this codebase), with review and decisions at each phase rather than one unreviewed pass.
**ChatGPT** was also used separately, informally, for an early read-through of the
assignment (`NOTRAFFIC משימת בית.txt` in the repo); its analysis was not treated as
authoritative and is superseded by the `context.md`/`design.md` chain below.

## What was accepted as-is

- The core geometry model (point-to-segment distance for on-line/segment-membership;
  signed cross-product for strict-side classification; a single interpolation parameter
  driving both the spatial crossing point and the crossing timestamp) - proposed by Claude,
  verified by hand against all 8 worked examples before being accepted, then implemented
  unchanged.
- The single-pass scan structure (classification + on-line counting + validation in one
  loop) - proposed, reasoned through for edge cases, and implemented as designed.

## What was rewritten or corrected, and why

- **Endpoint tolerance for interpolated crossings** (`context.md` Finding 1): my own
  original assumption was that the 1px tolerance should *not* extend an interpolated
  crossing past a segment endpoint. When Claude presented the literal spec wording
  ("within the 1-pixel tolerance" appearing directly in the crossing-condition text), I
  reversed that assumption. This is the one place I overrode my own prior instruction based
  on the model surfacing a textual conflict rather than just implementing what I'd said.
- **Three design gaps found by a deliberate self-critique pass** (`critic.md`, run as a
  separate "hostile reviewer" role against the finished design before any code was
  written): (1) the crossing scan's boundary logic was undefined for more than one on-line
  sample between the strict-side boundaries; (2) the design claimed a single pass while
  describing two sequential stages elsewhere; (3) a numeric-overflow risk was accepted
  without specifying the exception-safety mechanism that would make that acceptance safe.
  All three were fixed in `design.md` before implementation began, and each has a
  corresponding regression test in the suite (`test_three_on_line_samples_between_strict_
  boundaries_raises_value_error`, an iteration-count instrumentation check recorded during
  implementation, and `test_extreme_magnitude_coordinates_do_not_leak_unhandled_exception`).
- **One test-authoring bug caught by the red/green loop itself**: an early tolerance-band
  test used a negative y-coordinate, which correctly failed validation for the wrong reason
  (it should have tested exact-line interpolation, not negative-coordinate rejection) -
  caught immediately because the failure trace didn't match the test's intent, and fixed by
  changing the test's coordinates, not the implementation.

## Why

Every ambiguous point in the spec (tolerance semantics, endpoint behavior, validation vs.
performance trade-offs) was surfaced as an explicit decision with the reasoning shown before
being accepted, rather than silently resolved - so I can defend each choice in the
follow-up interview, and so any AI-proposed interpretation that conflicted with the literal
spec text or with an internal design decision was caught before it reached code.
