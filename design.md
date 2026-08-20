# design.md — NoTraffic RLR Assignment

> Source-of-truth precedence used throughout: (1) the assignment PDF, (2) `context.md`'s accepted
> decisions, (3) `plan.md`'s phases/dependencies.

> **Revision note.** This version incorporates fixes for all three objections raised in the
> independent review at `critic.md`: (1) Phase 3's boundary-detection logic is now explicitly
> defined for malformed inputs with more than one on-line sample, not just the well-formed case
> (Objection 1, High); (2) validation and geometric classification are now specified as a single
> interleaved pass rather than two sequential stages, resolving a self-contradiction between the
> "Validation versus performance" and Phase 4 sections (Objection 2, Medium); (3) the
> exception-safety boundary is now a specified mechanism, not just an asserted outcome (Objection
> 3, Critical). No accepted assumption from `context.md` (A1–A8, F1–F8) was reopened or changed.

## 1. Design goals

- **Correctness against the exact "if and only if" crossing definition**: both strict sides
  visited AND the transition geometrically within the finite segment (tolerance-inclusive per
  Finding 1) — neither condition alone is sufficient.
- **Clean separation of concerns**: geometry (pure math, no awareness of `RLRRequest`/
  `ValueError`), validation (pure shape/range checking), and orchestration (sequencing + the
  exception boundary) are three independent, independently testable layers.
- **Total behavior**: every input produces either a valid `RLRResult` or a `ValueError` — never
  any other exception, never a silently wrong result.
- **Finite-segment correctness**: every "is this on the stop-line" test — for a raw sample or an
  interpolated crossing — is measured against the actual finite segment, never the infinite
  extension.
- **Correct interpolation**: geometrically sound, exact-line based, with time interpolated using
  the same parametrization as space.
- **Scalability to 100,000-point trajectories**: O(n) time, O(1) auxiliary space, single pass.
- **Readability/explainability**: every non-obvious choice traceable to a named decision in
  `context.md`, defensible in the follow-up interview.

---

## 2. Inputs, outputs, and behavioral contract

### Specification guarantees
- `RLRRequest(car_id, stop_line, trajectory)` / `RLRResult(car_id, crossing_timestamp)` exactly
  as given.
- Trajectory points sorted ascending by `t`; timestamps unique (relied upon, not validated — A6).
- Vehicle crosses at most once; side sequence changes at most once (relied upon, not validated —
  F3).
- `y` not guaranteed monotonic; stop-line not guaranteed horizontal; trajectory need not start/end
  off the line.

### Validation requirements (must produce `ValueError`)
- Stop-line with two identical points (exact equality — F5).
- `car_id` empty, non-string, or whitespace-only (A8).
- Any negative coordinate (stop-line or trajectory).
- Any non-numeric / NaN / infinite coordinate or timestamp (A5 extends this to timestamps).
- A structurally malformed trajectory point (wrong arity, `None`).
- More than one trajectory sample classified on-line, regardless of position.
- (Vertical stop-lines are explicitly **not** an error — must be supported.)

### Accepted design assumptions (from `context.md`)
A1–A8 and F1, F5–F8 — full detail in the Assumptions register below; treated here as fixed
inputs, not reopened.

### Out-of-scope / possible Part 2 behavior
Side-change-guarantee defensive validation (F3), timestamp sort/uniqueness validation (A6),
numeric-overflow backstop on intermediate values (F8), and every item in `context.md` §4
(unsorted/duplicate timestamps, multiple crossings, streaming, larger n, configurable tolerance,
multiple/dynamic stop-lines, noisy trajectories).

---

## Phase 1 — Finalized behavioral/design decisions

**Purpose:** `context.md` is a chronological log with superseded text deliberately kept for
history — not itself something a reader could implement from directly. This phase resolves
"which version is current" once, so later phases have a single reference.

**Design:** Produce one closing statement in `context.md` enumerating, for every one of A1–A8 and
F1–F8, the *final* value only. This also formally closes the two flags raised during planning:
confirms Finding 1's Interpretation B (uniform tolerance) as final, and confirms Finding 2's
segment-distance-based on-line test (not the alternative found in the Hebrew-language reference
file) as final. No new geometric or algorithmic decision is made here — pure consolidation.

**Dependencies:** None.

**Verification:** Re-derive, from the closed contract alone, the expected output for all 8 worked
examples by hand; confirm each matches the spec's stated value. Paper-only check.

**Success criteria:** Every one of A1–A8/F1–F8 has exactly one unambiguous current value stated;
both flags are marked resolved-final; hand-derivation of all 8 examples from the closed contract
matches every expected output.

**Failure criteria:** Any item still reads ambiguously; a hand-derivation disagrees with a worked
example (meaning the contract itself, not just its presentation, is wrong).

---

## Phase 2 — Unit-test definition

**Purpose:** Guarantee tests define expected behavior rather than implementation defining it
retroactively, and give later phases a fixed target.

**Design:**
- *Data model scaffolding*: `RLRRequest`/`RLRResult` exactly as specified; a small package
  (`rlr/` with focused modules) rather than one file, since Phase 3/4 need independently
  testable geometry/validation/algorithm modules.
- *Test matrix*: one `TestCase` per concern (worked examples; must-raise conditions;
  must-return-`None` conditions; geometric edge cases; totality/exception containment; a
  large-trajectory smoke test) rather than one flat class. Each worked example asserts the exact
  expected `crossing_timestamp` with an epsilon-tolerant comparison (consistent with F7 — not
  exact float equality, since interpolation involves division). Each must-raise condition asserts
  `ValueError` by type only (message text is not part of the contract). Edge-case tests
  (graze-and-retreat, on-line sample surrounded by same side, vertical stop-line, a
  just-inside/just-outside-tolerance pair, three-or-more on-line samples, and an
  extreme-magnitude-coordinate totality case) are derived directly from the Geometry design
  section and from `critic.md`'s Objections 1 and 3. A large-trajectory test (~100,000 points)
  checks correctness on a constructed synthetic trajectory, not a strict timing assertion.

**Dependencies:** Phase 1 (contract closed before tests are written against it).

**Verification:** Cross-check the test matrix against the Testability section's rule list, line
by line. Confirm the suite fails at this point (nothing implemented) — the expected state.

**Success criteria:** Every rule in Testability has ≥1 named test; the suite is syntactically
complete and collectable by `python -m unittest`, even though every test currently fails/errors.

**Failure criteria:** A contract rule has no corresponding test; a test's expected value can't be
justified from the contract (guessed, not derived); the suite can't even be collected for reasons
unrelated to missing implementation.

---

## Phase 3 — Core implementation

**Purpose:** Implement crossing-detection for well-formed input before the malformed-input
validation layer, so the hardest part (geometry + single-pass algorithm) is designed and verified
in isolation from input-hardening concerns.

**Design:**
- *Geometry primitives* (full reasoning in the Geometry design section): independent, pure
  functions — point-to-segment distance (reused for both raw-sample on-line classification and,
  per Finding 1, interpolated-crossing segment-membership), signed side relative to the infinite
  line, and the interpolation parameter between two opposite-side points. No awareness of
  `RLRRequest`/`ValueError`/`car_id`.
- *Crossing-detection scan* (full reasoning in Interpolation design and State and invariants): a
  single left-to-right pass that classifies each point (on-line / strict-side-A / strict-side-B)
  and maintains running state sufficient to determine, at the end: whether both strict sides were
  seen; if so, the two boundary points bracketing the one guaranteed transition; and whether that
  transition is a same-sample case or an interpolation case, per the adjacency lemma. This layer
  also naturally counts on-line samples (consumed by Phase 4) but does not itself raise
  `ValueError` — it stays validation-free. The adjacency lemma's two-case dispatch (same-sample
  vs. interpolation) is valid only while the running on-line count is ≤1; the scan must remain
  total (never raise, never hit an undefined branch) even when that count is exceeded — see
  "State and invariants" for the exact fallback rule this requires.

**Dependencies:** Phase 1 (contract); internally, the scan depends on the geometry primitives
existing first (an ordering within this phase, not a cross-phase dependency).

**Verification:** Hand-compute the geometry primitives against all 8 worked examples' coordinates
and confirm exact agreement with the diagrams' distances/side labels. Run the full scan against
all 8 examples and confirm the returned timestamp/`None` matches within Finding 7's epsilon.
Reason through each geometric edge case in Geometry design (near/beyond endpoints, exact-1px
boundary, vertical/tilted lines) without running code.

**Success criteria:** All 8 examples produce the exact expected value; the scan is demonstrably
O(n) time / O(1) auxiliary space by inspection; vertical and tilted lines produce correct results
with no orientation-specific branch.

**Failure criteria:** Any example disagrees with its expected value; the scan needs more than one
pass or materializes O(n) auxiliary state; a special case is needed for vertical/horizontal lines
(a sign the geometry is slope-based, contradicting Finding 6); two structurally equivalent inputs
produce inconsistent classification.

---

## Phase 4 — Validation and robustness

**Purpose:** Harden the already-correct Phase 3 logic against malformed input, keeping "is this a
valid crossing" (Phase 3) fully separate from "is this request well-formed" (this phase).

**Design:**
- *Structural & value validation, interleaved into Phase 3's single loop*: every check that
  doesn't need geometry — `car_id` and stop-line-level checks (shape, whitespace, identical
  endpoints) run once, up front, since they don't depend on any trajectory point. Per-point
  checks (numeric validity, NaN/infinite/negative rejection, structural shape/arity) run
  *inside* the same loop iteration that Phase 3 uses to classify that point — validate sample
  `i`, then classify sample `i`, then advance to `i+1` — rather than as a separate prior scan
  over the whole trajectory. This is a single pass over the trajectory list, not two: the
  distinction is per-iteration ordering (validate-then-classify), not a separate traversal.
- *On-line-count enforcement*: inherently needs geometry, so it can't be decided before
  classification. The same loop increments an on-line counter as it classifies each point; after
  the loop completes, a count greater than one is converted into `ValueError`. Pipeline (one
  pass): for each point — structural/value check → geometric classification → running-state
  update (side/on-line bookkeeping, on-line count) → next point; after the loop — count check →
  result.
- *Malformed-count fallback inside the same pass*: if the running on-line count exceeds one at
  any point during the loop, the loop continues to completion (it must still finish validating
  every remaining point, per Assumption 1) but stops attempting to track or update transition-
  boundary state once the count exceeds one — see "State and invariants" for the precise rule.
  This keeps Phase 3's boundary logic from ever being asked to interpret a boundary gap the
  Adjacency Lemma doesn't cover.
- *Exception-safety boundary (mechanism, not just outcome)*: `process_request`'s outermost frame
  wraps the entire single-pass pipeline in one catch-all boundary — any exception type other than
  the `ValueError` instances intentionally raised by validation or the count check is caught and
  re-raised as `ValueError`. This is what makes Finding 8's accepted decision survivable: no
  numeric-overflow *backstop* is added around intermediate geometry values (the disclosed residual
  risk that extreme-but-finite coordinates could produce numerically meaningless results stands),
  but that risk can no longer surface as an uncaught, non-`ValueError` exception — only as a
  `ValueError` or a (possibly numerically meaningless, but syntactically valid) result.

**Dependencies:** Phase 2 (data model), Phase 3 (geometry + scan, for the on-line-count check).

**Verification:** Run every must-raise scenario against the full pipeline, confirm `ValueError`
in each case; run every must-return-`None` scenario, confirm a normal `RLRResult` is still
returned; construct an input designed to hit a non-`ValueError` exception if the catch-all
boundary were missing (e.g. a malformed point that would otherwise throw `TypeError` in geometry,
or an extreme-magnitude coordinate that overflows during geometric classification) and confirm it
instead raises `ValueError`; construct a trajectory with three or more on-line samples and confirm
the loop still completes and still raises `ValueError` rather than hitting an undefined
boundary-tracking case; inspect the implementation to confirm structural validation and geometric
classification occur within one loop over the trajectory, not two.

**Success criteria:** Every must-raise condition raises `ValueError` and nothing else; every
must-return-`None` condition returns a valid result; no scenario raises any other exception type;
a trajectory is iterated exactly once regardless of how many malformed conditions it contains.

**Failure criteria:** A malformed scenario raises a non-`ValueError` exception or fails to raise;
a well-formed input incorrectly raises (validation too strict); the implementation requires two
separate traversals of the trajectory; the exception boundary swallows genuine bugs as
false-`ValueError`; a trajectory with more than one on-line sample causes the loop itself to raise
an exception other than the final, intended `ValueError`.

---

## Phase 5 — Worked-example driver behavior

**Purpose:** Satisfy the spec's driver requirement — demonstrate the happy path (worked examples)
and the unhappy path (malformed input handled per-request without aborting).

**Design:** A sequential driver over a fixed list: the 8 worked examples plus at least one
deliberately malformed request (chosen from the must-raise contract, e.g. a negative coordinate,
so its failure is self-evidently expected). Each request runs inside a per-request
`try/except ValueError`, printing the resulting timestamp or a clearly labeled error, then
continuing regardless of outcome. Worked-example output includes enough detail (which example,
expected vs. actual) to make a mismatch visible without the test suite.

**Dependencies:** Phase 4 (complete public API + exception boundary).

**Verification:** Manual execution — read printed output, confirm all 8 values match expected,
confirm the malformed request is reported (not silently skipped, not crashing) and the driver
reaches the end of its list.

**Success criteria:** Driver runs to completion in one execution; all 8 outputs match; the
malformed request produces a visible, labeled error without stopping subsequent processing.

**Failure criteria:** Driver crashes before the end of the list; a worked-example output is
silently wrong; the malformed request is processed as valid or crashes the driver.

---

## Phase 6 — Documentation

**Purpose:** Satisfy the README/NOTES deliverables and transfer `context.md`'s reasoning into a
form defensible to a reader who isn't the assignment's author.

**Design:** `README.md` covers install/run instructions (trivial, stdlib-only) and a dedicated
"Assumptions beyond the spec" section mirroring the Assumptions register below — one entry per
A1–A8/F1–F8, stated as a plain-language rule plus one-sentence justification, not a replay of
`context.md`'s back-and-forth. `NOTES.md` is a separate, strictly ≤1-page AI-usage disclosure:
which tools were used (this design/planning session, and the separate Hebrew-language ChatGPT
analysis found in the repository), what was accepted as-is, what was materially rewritten and
why — a factual account, not a design justification (that belongs in README).

**Dependencies:** Phase 4 and Phase 5 (README's run instructions must reflect the final API and
driver); NOTES.md follows README since it reflects on the whole completed process.

**Verification:** Have someone unfamiliar follow README literally (install → test → run) and
confirm no missing step; check NOTES.md's length and required disclosure points.

**Success criteria:** README's instructions are self-sufficient; every Assumptions-register entry
has a corresponding README line; NOTES.md is ≤1 page and covers usage, acceptance, correction.

**Failure criteria:** A README instruction is missing a prerequisite; an assumption exists with no
README disclosure; NOTES.md exceeds one page or omits a required disclosure point.

---

## Phase 7 — Final verification

**Purpose:** Confirm the deliverable set is correct as a *whole* — earlier phases verify their own
slice; integration drift (e.g. documentation no longer matching actual behavior) is only caught
here.

**Design:** A checklist-driven pass, not new design work: run `python -m unittest` from the repo
root and confirm a clean pass; run `python main.py` and re-confirm Phase 5's criteria end-to-end;
re-read README/NOTES against the actual final code and correct any drift; confirm both planning
flags are reflected accurately in the final README disclosure.

**Dependencies:** All prior phases.

**Verification:** This phase *is* the verification step for the whole project.

**Success criteria:** `python -m unittest` passes with zero failures from a clean checkout;
`main.py` output matches Phase 5's criteria; no documentation claim is contradicted by the code.

**Failure criteria:** Any test fails; `main.py` crashes or mismatches a worked-example value; a
documentation claim is stale relative to the implementation.

---

## Geometry design

Three geometric objects, used for exactly one purpose each:

1. **Infinite supporting line** — the line through stop-line endpoints A and B, unbounded. Used
   *only* to determine which half-plane ("side") a strict (non-on-line) point falls into.
2. **Finite stop-line segment** — the literal segment from A to B. Used for the ≤1px on-line/
   on-segment tolerance test, for both raw samples *and* (per Finding 1) interpolated crossing
   points. The only place "finiteness" matters geometrically.
3. **The ≤1px tolerance band** — not a separate object, but a threshold on the finite-segment
   distance from (2). Because that distance is a clamped projection, the tolerance region forms a
   capsule/stadium shape: a corridor between the endpoints plus a rounded 1px cap beyond each one.

**Point-to-segment distance:** project P onto the infinite line through A, B; clamp the projection
parameter to `[0, 1]` so the projection point never leaves the segment; take the Euclidean
distance from P to that clamped point. Reused for both on-line classification and (Finding 1)
interpolated-crossing segment-membership.

**Sampled point classification:** apply point-to-segment distance; if `≤ 1 + epsilon` → on-line
(neither side); otherwise strictly one side, per the side test below.

**Strict-side classification:** for points already known not on-line, compute the signed cross
product of `(B−A)` and `(P−A)`; the *sign* (not magnitude) determines the side — independent of
position along the line's direction, so a point "beyond" an endpoint (Example 6) still has a
well-defined side.

**Horizontal stop-lines:** no special case — the vector formulas reduce naturally when `B−A` has
zero y-component.

**Vertical stop-lines (`x1==x2`):** explicitly required to be supported — again no special case in
the vector/cross-product formulation; a slope-based (`dy/dx`) formulation would divide by zero
here, which is exactly why Finding 6 rules that approach out.

**Arbitrary tilted stop-lines:** the general case the vector formulas are built for; horizontal
and vertical are simply the axis-aligned special cases of the same math, not separate paths.

**Points near endpoints** (within the capsule's rounded cap): classified via the same clamped
distance formula as points near the segment's middle — no distinct logic.

**Points beyond endpoints** (outside the 1px capsule): classified strictly by side; distance from
the segment is large, but side is still well-defined via the infinite-line cross product.

**Crossing between samples:** see Interpolation design.

**Exact sampled crossing:** when the transition lands on an on-line sample, no additional
geometry is needed — on-line, by construction, already implies within-segment-tolerance (see
State and invariants for why this case never needs a separate finite-segment check).

**Graze-and-retreat:** an on-line sample whose strict-side neighbors are the same side on both
sides is, by the crossing definition's first condition, never a crossing — falls out of the
"both sides visited" bookkeeping with no distinct "graze" concept needed.

**Reaching the line and stopping:** equivalent to a trajectory whose only strict side observed is
the one it approached from — falls out of the same bookkeeping.

**Crossing the infinite extension outside the segment:** the interpolation math always finds where
the sample-to-sample segment crosses the infinite line; whether that's a *valid* crossing is
decided solely by the same finite-segment-distance test used everywhere else — a point far beyond
the endpoint fails that test and yields `None`, with no distinct "outside the segment" code path.

---

## Interpolation design

**When required:** only when the guaranteed single transition falls between two adjacent
trajectory samples on strictly opposite sides, with no on-line sample between them (see the
adjacency lemma in State and invariants). If exactly one on-line sample sits between the two
differing-side samples, no interpolation is needed — the sample-transition rule applies instead.
If *more than one* on-line sample would sit between them, interpolation is not attempted at all —
per the on-line-count-exceeded fallback in State and invariants, the scan abandons transition
tracking entirely once the count exceeds one, and Phase 4 raises `ValueError` unconditionally.

**Qualifying samples:** exactly the two boundary samples identified by the single pass — the last
sample before the transition on the "before" side, and the first sample after it on the "after"
side.

**Geometric quantity determining crossing location:** the parameter along the straight segment
connecting the two boundary samples (in x,y space) at which that segment crosses the infinite
supporting line, found from the two samples' signed cross-product values (opposite sign, by
construction). Because the values have opposite signs, this parameter is guaranteed to fall
strictly between the two samples — no division-by-zero, no defensive clamp needed:

```
alpha = cross(A, B, P1) / (cross(A, B, P1) - cross(A, B, P2))   # in (0, 1), since signs differ
```

**Crossing timestamp:** the *same* `alpha` is applied to the two samples' timestamps —
`t = t1 + alpha * (t2 - t1)` — treating motion between consecutive samples as linear in space and
time simultaneously, matching "interpolate linearly between those two samples." Using a
separately-derived time parameter would have no geometric justification and was verified by hand
against Examples 1 and 3 during this design pass to match their expected values (12.5 and 12.35).

**Finite-segment membership check:** apply the same point-to-segment distance test used everywhere
else to the spatial crossing point; if it exceeds `1 + epsilon`, this is not a valid crossing and
the result is `None` regardless of both strict sides being visited (Example 6's exact scenario).

**Vertical and tilted lines:** the cross-product `alpha` formula makes no reference to slope, so
it applies unchanged to horizontal, vertical, and tilted lines — deliberately avoiding
convenient-but-unnecessary special-casing by x or y specifically (interpolating "by y" only works
for non-horizontal lines; "by x" only for non-vertical; the cross-product parametrization needs
neither).

---

## Validation design

Kept strictly separate from crossing detection: validation answers "is this request well-formed,"
never "did the vehicle cross."

**Structural/value layer** (no geometry): rejects invalid `car_id` (empty, non-string, or
whitespace-only — A8) and an identical-endpoint stop-line (exact equality — F5) up front, once,
before any trajectory point is examined; and rejects any negative coordinate, any
non-numeric/NaN/infinite coordinate, any non-numeric/NaN/infinite timestamp (A5, extending the
spec's "coordinates" wording to timestamps as an explicit accepted assumption), and any
structurally malformed trajectory point (wrong arity or `None`) per-point, interleaved into the
same loop iteration that Phase 3 uses to classify that point — validation of a point always
precedes classification of that same point, but this is enforced by intra-iteration ordering, not
by a separate traversal of the trajectory first.

**On-line-count layer** (needs geometry): consumes the on-line count already produced as a side
effect of Phase 3's single pass; converts a count greater than one into `ValueError`. Deliberately
not a second scan — see Phase 4's Design for the exact interleaving and the fallback that keeps
the scan total when the count is exceeded mid-pass.

**Explicitly not validated** (relying on stated guarantees):
- timestamp ascending order and uniqueness (A6) — the spec states this may be relied upon.
- "side changes at most once" (F3) — likewise relied upon; if violated, the single-pass design
  still terminates with a definite, non-crashing result (see State and invariants), so total
  behavior is preserved even though the *meaning* of the result under a guarantee violation is
  unspecified by the assignment.
- coordinate magnitude bounds beyond "not negative, not NaN, not infinite" (F8) — the disclosed
  residual overflow risk is accepted, not defended against.

---

## Validation versus performance

**Work required for complete validation:** the structural/value layer is O(1) per point — O(n)
total, unavoidable, since every point must be structurally sound before any other guarantee can
be relied upon.

**Work required for finding the crossing:** also O(1) per point (one distance-to-segment
computation, and — only for strict points — one cross-product sign) — O(n) total, and this cannot
be reduced below O(n) by exploiting "changes at most once," because the on-line-count validation
rule independently forces a full scan regardless of how quickly the crossing itself could
otherwise be located (Assumption 1's conclusion, reaffirmed by this design).

**Resulting total time complexity:** O(n) — a single pass performs both jobs simultaneously, in
the literal sense that each loop iteration validates sample `i` and then classifies sample `i`
before advancing, rather than validation and classification being two separate traversals of the
trajectory. (An earlier version of this document described these as one pass while Phase 4's own
pipeline described two sequential stages — that inconsistency is resolved by specifying the
interleaving explicitly here and in Phase 4's Design section; see `critic.md` Objection 2.)

**Extra-space complexity:** O(1) beyond the input list itself — the running state (first strict
side seen, the two boundary samples, on-line count and the one permitted on-line sample's data)
is a fixed, small number of scalars regardless of trajectory length; no per-point classification
array is materialized.

**Where the structural assumption still provides value:** not in asymptotic time complexity (O(n)
is unavoidable either way, per Finding 4), but in (a) allowing a single pass instead of multiple
passes or a search structure, keeping constant factors low and the implementation simple, and (b)
providing the correctness guarantee that "first differing-side boundary" bookkeeping is
sufficient — without the guarantee, a correct implementation would need to detect and reason
about multiple candidate transitions.

---

## State and invariants

While scanning the trajectory once, left to right:

- **On-line count** — samples classified on-line seen so far; must not exceed one (checked after
  the scan completes, per Phase 4, not mid-scan, so the full count is known before deciding).
- **First strict side** — the side label of the first strictly-classified sample encountered
  (undefined until one is seen); establishes the "before" reference.
- **Transition boundary state** — whether a differing strict-side sample has been seen, and if
  so, which two samples bracket the change. Because the trajectory is guaranteed to change side
  at most once (relied upon per F3), this boundary, once found, is never re-examined or replaced.
- **Adjacency lemma** (justifies the Interpolation design case split): between the two boundary
  samples, the only samples that can appear are on-line samples — never a third strict-side
  sample of either side, since that would imply a second side change, excluded by the relied-upon
  guarantee. Combined with the on-line-count limit of one, the two boundary samples are either
  directly adjacent (interpolation case) or separated by exactly one sample, which must be the
  single permitted on-line sample (sample-transition case). **This lemma's two-case dispatch is
  conditioned on the running on-line count being ≤1 at the time the transition is resolved — a
  fact the scan itself is tracking, not a fact guaranteed to be true of arbitrary (possibly
  malformed) input.** It is not safe to assume the lemma's precondition holds, because Phase 3 is
  explicitly required to run to completion on malformed input too (Phase 4 inspects its output
  afterward).
- **On-line-count-exceeded fallback (closes the gap the lemma leaves open):** the instant the
  running on-line count exceeds one, the scan stops attempting to identify or update transition-
  boundary state for the remainder of the trajectory — it no longer tries to decide "sample-
  transition vs. interpolation" at all. It continues only far enough to keep incrementing the
  on-line count and completing any remaining structural/value checks on later points (both
  required regardless, per Assumption 1), and reports a fixed, well-defined placeholder outcome
  (e.g. "no determinable crossing") for its own transition-related state. This placeholder is
  never returned to the caller: Phase 4's count check unconditionally overrides it with
  `ValueError` whenever the count exceeds one. No case with more than one on-line sample ever
  reaches the adjacency lemma's two-case dispatch.
- **Malformed-input flag** — whether the structural/value layer has already rejected the request
  outright (`car_id` or stop-line-level checks, which run once up front — see Phase 4); if so, the
  per-point loop does not run at all.

These are conceptual invariants the implementation must preserve, not a variable-naming or
data-structure prescription.

---

## Testability

Each item below is a required test category (Phase 2's matrix must cover every line):

- All 8 worked examples, exact expected `crossing_timestamp` (epsilon-tolerant comparison).
- A valid interpolated crossing on horizontal, vertical, and tilted lines (only horizontal/tilted
  are covered by the 8 examples — vertical needs a dedicated constructed case).
- A valid sampled (non-interpolated) crossing (Example 5, plus one additional constructed case
  with a differently-shaped stop-line).
- No crossing — trajectory never reaches the line (Example 2).
- Touch-and-stop (Example 4).
- Graze-and-retreat (Example 7).
- Crossing outside the finite segment via the infinite extension (Example 6).
- Endpoint boundary behavior — a constructed pair just inside vs. just outside Finding 1's
  capsule tolerance near an endpoint.
- Exactly-1px and just-outside-1px tolerance for a raw sample — targeting Finding 7's epsilon.
- Every must-raise condition (Example 8, plus one constructed case per remaining condition:
  empty/non-string/whitespace `car_id`, identical stop-line points, negative coordinate,
  non-numeric/NaN/infinite coordinate, non-numeric/NaN/infinite timestamp, malformed point shape).
- Multiple on-line samples (Example 8 directly, exactly two).
- **Three or more on-line samples**, positioned so they sit between the two strict-side boundary
  points — targets the on-line-count-exceeded fallback in "State and invariants"; confirms the
  scan completes and raises `ValueError` rather than hitting an undefined boundary case.
  (`critic.md` Objection 1.)
- A large trajectory (~100,000 points) — correctness-under-scale smoke check; also used to confirm
  by inspection/profiling that the trajectory is traversed once, not twice (`critic.md`
  Objection 2).
- Totality/exception containment — a scenario engineered to hit an unusual internal path (e.g. a
  malformed point that would otherwise throw `TypeError` in geometry), confirming only
  `ValueError` is ever observed.
- **Extreme-magnitude but structurally legal coordinates** (finite, non-negative, but large enough
  to overflow during geometric classification) — confirms the catch-all exception boundary holds:
  only `ValueError` or a valid result is ever observed, never a crash. (`critic.md` Objection 3.)

---

## Error-handling design

`process_request` is the sole exception boundary: the structural/value layer raises `ValueError`
directly for its own violations; the on-line-count check raises `ValueError` after the single pass
completes; nothing else is expected to raise. That expectation is not left as an unenforced
assumption: `process_request`'s outermost frame wraps the entire single-pass pipeline in one
explicit catch-all boundary — any exception type other than the `ValueError` instances
intentionally raised above is caught and re-raised as `ValueError`. This is the specific mechanism
(not merely a stated outcome) that upholds totality even under Finding 8's accepted residual risk:
geometry is not defensively checked for intermediate overflow (that decision stands), but the
catch-all boundary guarantees that if overflow ever does produce an internal failure — e.g. an
unhandled `NaN` reaching a branch that raises `AssertionError`, `IndexError`, or similar — the
caller still only ever observes `ValueError` or a valid `RLRResult`, never a raw internal
exception. The boundary must not swallow errors so broadly that it hides genuine implementation
bugs during development (e.g. it should still be possible to run the pipeline directly, without
the boundary, for debugging) — but in the boundary's normal, wrapped configuration, nothing
escapes `process_request` except `ValueError` or a valid result.

`main.py` builds on top of this rather than duplicating it: because `process_request` is already
guaranteed total, the driver's loop needs only one `try/except ValueError` per request — catch,
report which request failed and why, continue to the next item, never letting one bad request
block the rest.

---

## Assumptions register

### Design assumptions

| Ref | Assumption | Why necessary | Behavior affected | Documentation destination | Part 2 candidate? |
|---|---|---|---|---|---|
| A1 | Full trajectory must be scanned regardless of crossing-search speed | On-line-count validation independently forces O(n) | Confirms single-pass design; no complexity shortcut exists | Design explanation (Validation vs performance) | No — direct consequence of the validation contract |
| A2/A3 | Interpolation targets the exact mathematical infinite line, not a fuzzy band | Spec separates sampled tolerance from interpolation mechanics | Interpolation math is exact; only the *result*'s segment-membership is tolerance-checked | Design explanation | No |
| A4→F1 | Interpolated crossings share the raw-sample 1px segment-distance tolerance (revised from the stricter original reading) | Literal spec ties condition 2's segment test to "within the 1-pixel tolerance" | A crossing up to 1px beyond an endpoint is valid | README assumption | Possibly — shared-endpoint tolerance ambiguity (context.md §4) |
| A5 | Timestamps must be numeric/finite/non-NaN | Spec's "coordinates" wording extended by inference to timestamps | Invalid timestamp → `ValueError` | README assumption | No |
| A6 | Timestamp order/uniqueness relied upon, not validated | Spec explicitly states this guarantee | No defensive check added | README assumption | Yes — listed in context.md §4 |
| A7 | No extra structural-type policing beyond what's explicitly required | Avoids inventing requirements | Normal API usage assumed | — | No |
| A8 | Whitespace-only `car_id` treated as empty | Literal spec only says "empty" | Whitespace-only strings raise `ValueError` | README assumption | No |
| F5 | Identical-endpoint check uses exact equality | 1px tolerance is textually scoped to trajectory points only | Only bit-for-bit identical endpoints raise `ValueError` | README assumption | No |
| F6 | Vector/cross-product geometry throughout, never slope-based | Vertical stop-lines are explicitly supported; slope formulas divide by zero | No orientation-specific branch anywhere | Design explanation | No |
| F7 | Small epsilon buffer (~1e-9) on the ≤1px comparison | Floating-point rounding could misclassify a true-boundary point | Boundary classification robust to representation noise | README assumption | No |
| F8 | No defensive finiteness backstop on intermediate geometry values | Declined; residual risk judged narrow | Adversarial, extremely large-but-finite coordinates could in principle silently overflow undetected | README assumption (disclose residual risk) | No — accepted, not deferred |

No item above is marked **DESIGN CONCERN** — this design review found no case where an accepted
assumption conflicts with another accepted assumption, a worked example, or the total-processor
requirement.

---

## Open issues

### Open design questions

None. Every question raised during analysis and planning (`context.md`'s F1–F8, and the two
flags raised during the planning phase) has an explicit, recorded resolution. This design pass
did not surface a new genuinely open question. The two flags are carried forward for
completeness, not because they remain unresolved:

- **Flag 1** (a planning prompt restated the *original* Assumption 4, not the revised one) —
  already reconciled in `plan.md` and in this design in favor of `context.md`'s Finding 1. No
  action needed.
- **Flag 2** (an independent, informal Hebrew-language ChatGPT analysis found in the repository
  describes on-line/side classification differently from `context.md`'s Finding 2) — this design
  follows Finding 2, confirmed against Example 6's diagram and hand-computed geometry for all 8
  worked examples during this design pass (Phase 3 Verification). No action needed.

---

## Part 2 considerations

### Possible Part 2 extensions

(Preserved from `context.md` §4; design impact noted, nothing designed or implemented here.)

- **Side-change guarantee removed** — would invalidate the single-boundary assumption in State
  and invariants; the scan would need to track multiple candidate transitions instead of one.
- **Unsorted or duplicate timestamps** — would invalidate the "process left to right, boundaries
  unambiguous by index order" framing throughout Phase 3; likely requires an explicit sort step or
  a redefinition of "transition."
- **Streaming trajectories** — the single-pass shape is streaming-friendly in principle (O(1)
  state), but the on-line-count validation currently requires seeing the whole trajectory before
  deciding malformed-vs-not; would need rethinking for a true incremental contract.
- **Much larger n (millions of points)** — the current O(n)/O(1) design already scales linearly;
  the practical limit would shift to per-point Python overhead, pushing toward vectorization
  (outside the stdlib-only constraint) rather than a design change.
- **Configurable/different tolerance** — would only require the ≤1px constant (plus Finding 7's
  epsilon) to become a parameter; the segment-distance-based geometry itself wouldn't change.
- **Multiple or dynamic stop-lines** — would require re-examining Finding 1's endpoint-capsule
  behavior where two stop-lines' tolerance regions could overlap (already flagged in context.md
  §4).
- **Noisy trajectories** — the current hard "at most one on-line sample" rule assumes clean
  single-graze behavior; noise could require a windowed/statistical rule instead of an exact count.

---

## Design readiness checklist

- Is the crossing definition unambiguous? **Yes** — both-strict-sides-visited AND
  transition-within-finite-segment, fully specified.
- Is sampled on-line classification unambiguous? **Yes** — finite-segment distance ≤ 1px +
  epsilon (Finding 2, Finding 7).
- Is strict-side classification unambiguous? **Yes** — signed cross-product relative to the
  infinite line (Finding 2, confirmed via Example 6).
- Is interpolation behavior unambiguous? **Yes** — exact-line cross-product-zero parametrization,
  applied identically to space and time (verified by hand against Examples 1 and 3 this session).
- Is finite-segment membership unambiguous? **Yes** — same segment-distance test reused for raw
  samples and interpolated crossings, per Finding 1.
- Are endpoint semantics unambiguous? **Yes** — 1px capsule tolerance beyond each endpoint, per
  Finding 1 (both interpretations on record; current one final).
- Are malformed-input rules unambiguous? **Yes** — fully enumerated, cross-checked against
  Example 8.
- Is the exception boundary defined? **Yes** — `process_request` wraps the single-pass pipeline
  in an explicit catch-all that converts any non-`ValueError` exception into `ValueError`; this is
  a specified mechanism, not just an asserted outcome (fixed per `critic.md` Objection 3).
- Is validation versus crossing-search complexity understood? **Yes** — both O(n), unified into
  one pass; no asymptotic shortcut exists given the on-line-count rule.
- Can every important behavioral rule be converted into a test? **Yes** — mapped exhaustively in
  Testability.
- Are Part 1 assumptions separated from possible Part 2 extensions? **Yes** — Assumptions
  register vs. Part 2 considerations kept distinct; no Part 2 behavior appears in any phase design.
- Is the design ready for the unit-test-definition phase? **Yes** — Phase 2 can proceed using this
  document as its reference.

No item above is `No` or `Needs decision`. This design is ready for implementation to begin at
Phase 2/Phase 3 per `plan.md`'s sequencing.
