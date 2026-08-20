# Implementation Plan — NoTraffic RLR Assignment

This plan sequences the work from the repository's current state (spec + `context.md` analysis
log only — no code, tests, or docs yet) through a complete, verified Part 1 submission. It is a
plan, not code: no step below specifies pseudocode, formulas, or concrete algorithm internals
beyond what `context.md` already records as decided.

**Repository state confirmed by inspection (this session):** the workspace contains
`NoTraffic_Take_Home_Part1_rev_2 (2).pdf` (spec), `context.md` (analysis log — authoritative
source of truth for all Part 1 decisions), `plan.md` (this file), `Prompt for home assignment.txt`
(the original analysis-session prompt), and `NOTRAFFIC משימת בית.txt` (a separate, informal
ChatGPT analysis in Hebrew, not part of the deliverables — see flag below). No `rlr/`, `tests/`,
`main.py`, `README.md`, or `NOTES.md` exist yet; every file referenced below is marked `NEW`.

## How to read this plan

Every item below is one of:
- **SPEC REQUIREMENT** — stated directly in the assignment PDF.
- **AGREED DECISION** — already resolved in `context.md` (assumptions A1–A8, findings F1–F8);
  treated here as an input, not reopened.
- **DECISION FOR THIS STEP** — genuinely still open; named, not made, per each step's "Decisions
  made in this step."
- **PART 2 — NOT IMPLEMENTED** — documented in `context.md` §4 as a possible future extension;
  explicitly out of scope for every step below.

---

## ⚠️ Flags — read before executing this plan

**Flag 1 — stale restatement of Assumption 4.** This planning prompt's "Existing agreed
assumptions" section asks to preserve "interpolated crossings being required to fall
geometrically inside the finite segment endpoints" — that is the *original* Assumption 4.
`context.md`'s Finding 1 explicitly revised this after presenting you with the literal-spec
conflict: the current agreed decision is the **opposite** — the same 1px tolerance used for
raw-sample classification also applies to interpolated crossings (Interpretation B), so a
crossing up to 1px past an endpoint is valid. This plan follows `context.md`'s latest resolution
(Finding 1) as authoritative, since it's the most recent explicit decision on record, not the
restated original. Flagging rather than silently reconciling, per this task's own instructions.

**Flag 2 — a differing geometric formulation found in the repository.** `NOTRAFFIC משימת
בית.txt` (an independent, informal ChatGPT analysis of the same assignment, found alongside the
spec) describes "on-line" and "side" as derived from a single signed-distance-to-the-**infinite**-line
function, with `|distance| ≤ 1` meaning on-line. `context.md`'s Finding 2 — confirmed directly
against Example 6's diagram — establishes two *separate* computations: on-line uses distance to
the **finite segment** (clamped, capsule-shaped near endpoints), while side uses the sign relative
to the infinite line. These formulations agree everywhere except near/beyond the endpoints, where
the Hebrew note's single-function approach would over-classify points as "on-line" that
`context.md`'s segment-distance approach (and the literal spec text: "distance to the **stop-line
segment**") would not. This plan follows `context.md`'s Finding 2. Not a decision this plan makes
silently — flagged for awareness since it's a real discrepancy between two AI-assisted analyses of
this assignment.

---

## Phase 1 — Finalized behavioral/design decisions

### Step 1 — Consolidate and close the Part 1 behavioral contract

**Goal:** Turn `context.md`'s chronological analysis log (which includes superseded text kept
for history) into one closed, unambiguous statement of the complete Part 1 contract, so every
later step has a single reference instead of needing to re-derive "which version is current."

**Decisions made in this step:**
- Whether any Part 1 behavioral question remains genuinely open beyond what `context.md`
  already resolved (A1–A8, F1–F8), after accounting for Flags 1 and 2 above.
- How the two flags above are recorded in the closed contract (as resolved-with-caveat vs.
  needing your explicit re-confirmation before Step 3 locks them into the test matrix).

**Files touched:** `context.md` (append a closing "Finalized Contract" section; append-only,
consistent with the log's own convention of preserving history rather than overwriting it)

**Dependencies:** None

**Completion criteria:** `context.md` contains one closing section that unambiguously states the
full Part 1 contract with no remaining open items, and both flags above are either explicitly
re-confirmed by you or explicitly carried forward as documented caveats — not silently dropped.

---

## Phase 2 — Unit-test definition

### Step 2 — Data model & package scaffolding

**Goal:** Establish the importable data model so the test matrix (Step 3) has concrete types to
import against, without yet implementing any behavior.

**Decisions made in this step:**
- Package layout — single module vs. a small package — and the resulting import surface.

**Files touched:** `NEW: rlr/__init__.py`, `NEW: rlr/models.py`

**Dependencies:** None

**Completion criteria:** `RLRRequest` and `RLRResult` are defined exactly per the spec's given
dataclass signatures and import cleanly; no processor logic exists yet.

### Step 3 — Test matrix definition

**Goal:** Encode the finalized contract (Step 1) as a complete, reviewable `unittest` suite
*before* any behavior is implemented, so the tests define expected behavior rather than
implementation defining it retroactively.

**Decisions made in this step:**
- How tests are grouped/organized (e.g., one `TestCase` per concern vs. per worked example).
- How the not-yet-implemented `RLRRequestProcessor` is referenced so the suite is structurally
  complete even though every test is expected to fail until Phase 3–4 land.

**Coverage this step must account for** (per the assignment and `context.md`):
all 8 worked examples; every explicit must-raise `ValueError` condition; every explicit
must-return-`None` condition; the geometric/boundary edge cases surfaced in `context.md`
(graze-and-retreat, an on-line sample surrounded by same-side points, a vertical stop-line, the
near-endpoint tolerance boundary per Finding 1, the floating-point boundary per Finding 7); and at
least one large-trajectory case exercising the up-to-100,000-point constraint.

**Files touched:** `NEW: tests/test_rlr_processor.py`

**Dependencies:** Step 1 (contract), Step 2 (data model to import)

**Completion criteria:** The suite is complete and each test is traceable to a specific line in
`context.md`'s finalized contract; running it now fails (nothing is implemented yet) — that
failure is itself the checkpoint confirming the tests were written from the contract, not from
implementation behavior.

---

## Phase 3 — Core implementation

### Step 4 — Geometry primitives

**Goal:** Implement the two distinct geometric computations `context.md`'s Finding 2 establishes:
on-line classification relative to the finite segment, and side classification relative to the
infinite line — incorporating the epsilon buffer (Finding 7) and vector-based handling for
vertical stop-lines (Finding 6, so no slope-based formula is used).

**Decisions made in this step:**
- How the two computations are exposed as functions and how their module boundary is drawn.
- How the epsilon buffer and vertical-line handling are incorporated internally.

**Files touched:** `NEW: rlr/geometry.py`

**Dependencies:** Step 1 (contract)

**Completion criteria:** The geometry functions exist and are independently invocable; manually
cross-checked against the numeric facts implied by the 8 worked examples (expected distances and
side labels), as a sanity check ahead of formal test coverage in Step 7.

### Step 5 — Crossing-detection algorithm (single pass)

**⚠️ RISKIEST STEP** — this is where every subtle, previously-reversed, or genuinely ambiguous
resolved decision (Finding 1's endpoint-tolerance reversal, Finding 2's dual-geometry split,
Finding 4's single-pass shape, Finding 7's epsilon) converges into actual control flow, making it
the most likely place for a correctness bug the worked examples might not fully expose.

**Goal:** Implement the single-pass scan (already decided in `context.md`, Finding 4) that
classifies each trajectory point using Step 4's geometry, determines whether both strict sides are
visited, locates the transition (at-sample vs. interpolated), and computes the crossing timestamp
under the Finding-1-revised endpoint-tolerance rule — resolving every `None`-producing case
(empty/single-point trajectory, one-side-only, reaches-without-proceeding, infinite-extension-only
crossing).

**Decisions made in this step:**
- The internal representation used to track per-point classification during the scan.
- Whether the on-line-count enforcement (a validation rule) is folded into this same pass or left
  for Phase 4 — this determines how Step 6/7 connect to this step.

**Files touched:** `NEW: rlr/processor.py` (algorithm portion only — not yet the public class)

**Dependencies:** Step 4

**Completion criteria:** A standalone function taking a validated stop-line and trajectory returns
`float | None` correctly for all 8 worked examples and the additional geometric edge cases,
verified by manually running it against the relevant cases from Step 3's suite even though the
public class isn't wired up yet.

---

## Phase 4 — Validation and robustness

### Step 6 — Structural & value validation layer

**Goal:** Implement every malformed-input check: `car_id` empty/non-string/whitespace-only (A8),
negative coordinates, non-numeric/NaN/infinite coordinates and timestamps (A5), structurally
malformed trajectory points (wrong arity, `None`), and the stop-line identical-points check
(Finding 5, exact equality).

**Decisions made in this step:**
- Where validation lives relative to the processor (separate module vs. inline).
- How/when it raises relative to Step 5's scan — specifically, whether the on-line-count check
  (which needs geometry) is enforced here as a dedicated pass, or was already folded into Step 5.

**Files touched:** `NEW: rlr/validation.py`

**Dependencies:** Step 2 (data model), Step 4 (geometry, needed for the on-line-count check)

**Completion criteria:** Validation raises `ValueError` for every must-raise condition in the
spec, verified against Step 3's malformed-input test cases.

### Step 7 — Total-processor integration & exception safety

**Goal:** Wire `RLRRequestProcessor.process_request` to sequence Step 6's validation and Step 5's
algorithm, and establish the top-level exception-safety boundary so nothing but `ValueError` can
ever escape — consistent with Finding 8's decision to rely on input-level validation only, without
adding numeric-overflow backstops on intermediate computed values.

**Decisions made in this step:**
- How validation and algorithm sequencing interact in practice (e.g., single combined pass vs.
  two passes) — this is where Assumption 1's distinction between "validation complexity" and
  "crossing-location complexity" gets locked into concrete control flow.

**Files touched:** `NEW: rlr/processor.py` (adds the public class on top of Step 5's algorithm),
`rlr/__init__.py` (export the public class)

**Dependencies:** Step 5, Step 6

**Completion criteria:** `RLRRequestProcessor.process_request` exists as the complete public API
described in the spec; this is the first point at which Step 3's full test suite can actually
pass.

---

## Phase 5 — Worked-example driver behavior

### Step 8 — `main.py` driver

**Goal:** Build the driver that runs the 8 worked examples and prints results, and feeds at least
one malformed request through the same loop, per the spec's explicit deliverable requirement.

**Decisions made in this step:**
- How the loop structures per-request error reporting so a caught `ValueError` is reported without
  aborting the run.

**Files touched:** `NEW: main.py`

**Dependencies:** Step 7

**Completion criteria:** Running `python main.py` prints all 8 worked-example results matching the
spec's expected values, plus a reported (non-fatal) failure for the malformed request, and the
process exits cleanly.

---

## Phase 6 — Documentation

### Step 9 — `README.md`

**Goal:** Document install/run instructions and every assumption made beyond the literal spec
(A1–A8, F1–F8), including both flags raised in this plan and their final disposition.

**Files touched:** `NEW: README.md`

**Dependencies:** Step 7, Step 8

**Completion criteria:** A reader can install, run the tests, and run `main.py` from README alone;
every entry in `context.md`'s decision register is represented.

### Step 10 — `NOTES.md`

**Goal:** Disclose AI-tool usage (≤1 page) per the spec's explicit requirement — which tools were
used across the exercise (including this planning session and the separate Hebrew-language
ChatGPT analysis found in the repository), what was accepted as-is, what was rewritten, and why.

**Files touched:** `NEW: NOTES.md`

**Dependencies:** Step 9

**Completion criteria:** ≤1 page; addresses all three disclosure points the spec requires (how AI
was used, which parts were AI-assisted, non-trivial corrections made to AI output).

---

## Phase 7 — Final verification

### Step 11 — End-to-end verification pass

**Goal:** Confirm the complete deliverable set satisfies the spec as a whole, not just
step-by-step.

**Decisions made in this step:** None — this is a checklist/verification pass, not a design
decision.

**Files touched:** None expected; may touch `README.md`, `NOTES.md`, or `context.md` only if
verification surfaces a small documentation gap.

**Dependencies:** Steps 1–10 (all)

**Completion criteria:** `python -m unittest` passes from the repository root; `python main.py`
runs clean and matches all 8 expected worked-example values; malformed-input handling doesn't
abort the driver; `README.md` and `NOTES.md` are present and accurate; both flags raised in this
plan are either resolved or consciously left as documented, disclosed decisions — nothing
undocumented remains.

---

## Part 2 — explicitly not implemented in this plan

Every candidate extension already logged in `context.md` §4 (side-change guarantee removed,
unsorted/duplicate timestamps, streaming trajectories, much larger n, configurable tolerance,
multiple stop-lines, dynamic stop-lines, noisy trajectories, shared-endpoint tolerance ambiguity)
remains out of scope for every step above. No step in this plan should introduce speculative
generality toward any of these.

---

## Smallest first step that would validate the rest of this plan

**Before Step 2 or Step 3 are even started:** a throwaway, uncommitted check of the geometry
primitives' core numbers — computing point-to-finite-segment distance and infinite-line side for
the exact coordinates in all 8 worked examples, applying the Finding-1-revised endpoint-tolerance
rule and the Finding-7 epsilon by hand or in a scratch script — and confirming every result matches
the spec's expected output.

- **What it validates:** the single riskiest cluster of decisions in the whole plan (Finding 1,
  Finding 2, Finding 6, Finding 7) simultaneously, and empirically settles Flag 2 — if
  segment-distance classification reproduces all 8 expected values, `context.md`'s Finding 2 is
  confirmed correct over the Hebrew note's differing formulation.
- **Why it comes first:** every other step (the test matrix, the validation layer, the driver, the
  docs) inherits whatever the geometric model turns out to be; getting this wrong is the one
  mistake that would force rework across nearly the entire plan.
- **What failure would mean:** if segment-distance classification does *not* reproduce all 8
  expected values, `context.md`'s Findings 1 and 2 need to be reopened with you before Step 1 is
  even closed out — not discovered later inside a half-built test suite or implementation.
