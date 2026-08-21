# NOTES.md - AI Usage

## Tools used

- **Claude Code** - used for the entire exercise: requirements analysis, design,
  self-critique, test planning, and implementation, as explicit reviewed phases
  (`context.md`, `plan.md`, `design.md`, `critic.md`, `tests.md`) before any code was
  written.
- **ChatGPT** - used for a preliminary analysis of the assignment, which informed and
  improved the detailed prompts it then helped draft; those prompts were given to Claude
  for each phase above and used to help produce the resulting `*.md` files and
  implementation.
- **Loop engineering (TDD)** - the implementation was built with a red/green test loop:
  add one small test, confirm it fails, write the minimum code to pass it, re-run the full
  suite, then move to the next slice - rather than writing all tests or all code up front.
- **pyproject.toml** - used to define the installable `rlr` package (no third-party
  dependencies); this file and the full project (code, tests, docs) were pushed to the
  public GitHub repository.

## What was accepted as-is

- Core geometry model - point-to-segment distance for on-line classification, signed
  cross-product for strict-side classification, one interpolation parameter driving both
  the crossing point and the crossing timestamp. Verified by hand against all 8 worked
  examples before acceptance, then implemented unchanged.
- Single-pass scan structure - classification, on-line counting, and validation combined
  in one loop. Reasoned through for edge cases, then implemented as designed.

## What was rewritten or corrected, and why

- **Endpoint tolerance for interpolated crossings** - original assumption barred a
  tolerance extension past a segment endpoint; reversed after the literal spec wording
  ("within the 1-pixel tolerance") was shown to contradict it.
- **Three design gaps from a dedicated self-critique pass**, fixed before any code was
  written:
  - Undefined behavior for 3+ on-line samples between the strict-side boundaries.
  - A self-contradictory "single pass" claim in the design document.
  - An unspecified exception-safety mechanism for an accepted numeric-overflow risk.
  - Each fix has a corresponding regression test or check in the suite.
- **One test-authoring bug** - an early tolerance test used an illegal negative
  coordinate; caught immediately by its own red/green failure and fixed by correcting the
  test, not the implementation.

## Why

- Every ambiguous point (tolerance semantics, endpoint behavior, validation-vs-performance
  trade-offs) was surfaced as an explicit, reasoned decision before acceptance.
- This makes each choice defensible in a follow-up interview and ensures no AI-proposed
  interpretation reached code unchecked.
