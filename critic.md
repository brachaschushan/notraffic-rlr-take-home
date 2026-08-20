# critic.md — Hostile Review of design.md

> Reviewer role: independent, adversarial. This document does not modify `context.md`,
> `plan.md`, or `design.md`. Source precedence used: (1) the assignment PDF, (2) `context.md`,
> (3) `plan.md`, (4) `design.md`. An assumption being recorded in `context.md` is treated as
> reviewable, not immune.

---

## Objection 1 — Phase 3's own stated invariant is only true for well-formed input, but Phase 3 must run on malformed input too

### 1. Sharp objection

`design.md`'s "State and invariants" section asserts that the two transition-boundary samples
are "either directly adjacent... or separated by exactly one sample" — but this claim depends on
the on-line count already being ≤1, a fact Phase 3 cannot know until *after* the pass Phase 4
uses to check it, so the design never specifies what Phase 3 does when that's false.

### 2. Why this matters

This is a correctness/robustness gap in Phase 3 combined with a sequencing error in the design's
own reasoning. `design.md`'s "Adjacency lemma" argument explicitly leans on "the on-line-count
limit of one" to prove only two cases are geometrically possible — but that limit is a
*validation rule* (Phase 4, "must raise `ValueError`" in the spec), not a guarantee the input
satisfies before validation runs. Phase 3 is explicitly designed to be "validation-free" (Phase 3
Design: "it stays validation-free") and to run to completion so Phase 4 can inspect its output
afterward (Phase 4 Design: "this phase inspects that count afterward"). That means Phase 3 *must*
run — and must not crash — on inputs where the on-line count is 2, 3, or more, i.e. exactly the
inputs the lemma assumes cannot occur. The design never states what the boundary-detection logic
does when more than one on-line sample sits between the two strict-side boundary points. This is
a specification gap in `design.md` itself, not merely an implementation detail: a design document
whose own stated invariant is conditioned on a fact not yet established at the point it's used is
not "detailed enough that another engineer could implement from it" (the document's own stated
goal in its header).

### 3. Concrete failure scenario

1. Stop-line `(5,100)-(15,100)`. Trajectory: `(10,8,98)` [side −], `(11,8,100)` [on-line, dist 0],
   `(12,9,100.3)` [on-line, dist 0.3], `(13,10,99.8)` [on-line, dist 0.2], `(14,8,102)` [side +].
2. Per the spec's malformed-input contract, this trajectory has three on-line samples, so
   `process_request` **must** raise `ValueError`.
3. But per `design.md`'s pipeline, Phase 3's scan runs first and must reach a result before Phase
   4's count check can override it. The scan's boundary-detection logic — as specified — only
   defines two cases: adjacent boundaries (interpolate) or boundaries separated by exactly one
   on-line sample (use its timestamp). A gap of three on-line samples matches neither case.
4. `design.md` does not say what happens next. A literal implementation of the two-case dispatch
   described in "Interpolation design" and "State and invariants" has no `else` branch — an
   implementer following the design as written could easily produce an unhandled code path.
5. If that path raises anything other than `ValueError` (e.g. an `IndexError` from an
   out-of-range lookup, or an `AssertionError` from a "this can't happen" guard), the spec's
   "no other exception may escape `process_request`" requirement is violated by a plausible,
   easily-constructed input — not an exotic one.

### 4. Proposed design change

Revise "State and invariants": state explicitly that the Adjacency Lemma holds **only under the
precondition that the on-line count is ≤1**, and add a new, separate rule for Phase 3's scan:
*when more than one on-line sample is encountered, Phase 3 must not attempt to select or
interpolate a transition at all — it must short-circuit to a safe, arbitrary, well-defined
placeholder result (e.g., treat the request as "no determinable crossing" for its own purposes)
and rely unconditionally on Phase 4's count check to override the result with `ValueError`.*
This makes Phase 3 total by construction for *every* on-line count, not just 0 or 1, and removes
the dependency of Phase 3's control flow on a fact only Phase 4 is responsible for checking.

### 5. Impact on tests

The "Multiple on-line samples" test category (currently only Example 8, with exactly two on-line
points) must be extended with a case using **three or more** on-line samples positioned so they
sit *between* the two strict-side boundary points — specifically targeting the code path this
objection identifies as unspecified.

### 6. Severity

**High** — not certain to manifest in every implementation (a careful engineer might handle the
"else" case correctly by instinct), but the design document as written does not rule out a
totality violation on a plausible, spec-relevant malformed input, and Phase 2's test matrix would
have no reason to catch it since Example 8 only exercises the two-on-line-point case.

---

## Objection 2 — The design claims "one pass" while its own pipeline describes two

### 1. Sharp objection

`design.md`'s "Validation versus performance" section states the structural-validation pass and
the geometric scan are "the same pass, not additive separate passes," but Phase 4's own "Design"
subsection describes them as sequential stages ("structural validation → single geometric scan"),
which is two passes over the trajectory, not one.

### 2. Why this matters

This is a performance-claim-accuracy and maintainability issue, not a correctness bug — but the
assignment explicitly asks evaluators to judge "whether your algorithm exploit[s] the structural
assumptions, or process[es] every point regardless," and `design.md` directly answers that
question with a claim its own text contradicts. Re-reading Phase 4 verbatim: "Pipeline: structural
validation → single geometric scan (classification + crossing search + on-line counting) → count
check → result." That is an explicit two-stage sequence: validate every point first, *then*
classify/scan every point. Two O(n) stages over the same input is still O(n) overall, so the
asymptotic claim ("resulting total time complexity: O(n)") is not wrong — but "the same pass, not
additive separate passes" is a specific, falsifiable claim about implementation shape, and it's
false given Phase 4's own description. This is exactly the "complexity statement that is
technically true but misleading" failure mode called out in the review brief.

### 3. Concrete failure scenario

1. An implementer builds Phase 3's scan and Phase 4's structural validation exactly as separately
   described (two distinct functions/loops, called in sequence, as Phase 4's pipeline literally
   describes).
2. At review or in the Part 2 interview, the candidate is asked to demonstrate the "single pass"
   design their document claims.
3. Profiling or code inspection shows the trajectory is iterated twice — once for structural
   checks, once for geometric classification — not once.
4. The candidate has no way to reconcile this with `design.md`'s explicit "not additive separate
   passes" claim without admitting the design document itself was imprecise, undermining
   confidence in the rest of the document's technical claims.
5. Separately: for a 100,000-point trajectory, this is a real (if modest) constant-factor cost —
   exactly the kind of thing the assignment's performance-focused evaluation criterion is
   designed to surface.

### 4. Proposed design change

Either (a) correct the "Validation versus performance" section to say the design uses **two**
sequential O(n) stages (still O(n) overall, but not a single pass), and justify why splitting
validation from geometry is worth the extra constant factor (defensibly: geometry must not run on
structurally-invalid points) — or (b) if a true single pass is desired, change Phase 4's Design
subsection to specify that structural/value validation of each point is interleaved *inside* the
same loop that performs Phase 3's classification (validate the current point, then immediately
classify it, before advancing), rather than as a separate prior stage. `design.md` must pick one
of these and state it as the actual pipeline shape — not both, as it currently does in different
sections.

### 5. Impact on tests

No new test category is strictly required (both variants are O(n) and behaviorally identical
under the test matrix), but the large-trajectory test's rationale/comment should record which
pipeline shape (one pass vs. two) the implementation actually uses, so a future reader isn't
misled the way this review was.

### 6. Severity

**Medium** — no correctness or robustness impact, but a self-contradiction inside the design
document about a claim the assignment explicitly asks candidates to be able to defend.

---

## Objection 3 — The design accepts a numeric-overflow risk (F8) without specifying the safety-net mechanism that would make that acceptance survivable

### 1. Sharp objection

`design.md`'s Error-handling section asserts `process_request` "guarantees" that only `ValueError`
or a valid result is ever observed, but never specifies a concrete mechanism (such as a
catch-all exception boundary) that would actually make that guarantee hold given F8's explicit
decision not to defend against intermediate-value overflow.

### 2. Why this matters

This is the most spec-critical objection of the three: the assignment bolds "Robustness — the
processor must be total" and explicitly says "In particular, non-numeric, `NaN`, or infinite
coordinates... must be rejected with `ValueError` — they must not be allowed to leak a
`TypeError`... nor to silently return a result." `design.md` correctly inherits F8's decision that
*input-level* NaN/Infinite/negative rejection is sufficient and that no defensive check is added
around *intermediate* geometry values (distance, cross-product, interpolation parameter) — a
reasonable, disclosed trade-off in `context.md`. But `design.md`'s Error-handling section then
asserts totality as an *outcome* ("process_request... guarantees") without pairing it with any
*mechanism*. IEEE-754 arithmetic does not raise on overflow; a finite-but-extreme coordinate can
silently produce `inf`/`nan` mid-computation, and what happens next depends entirely on how the
side/on-line classification logic is written — a detail `design.md` leaves unspecified. Asserting
an outcome without specifying the mechanism that produces it is not the same as designing for it.

### 3. Concrete failure scenario

1. Stop-line `A=(0, 0)`, `B=(1e200, 1e200)` — both coordinates finite, non-negative, and a
   non-degenerate (non-identical) pair, so structural validation (rejects negative/NaN/Infinite/
   non-numeric values) passes cleanly; nothing in the spec bounds coordinate magnitude.
2. A trajectory sample at similarly extreme magnitude is classified: computing
   `(Bx-Ax)*(Py-Ay) - (By-Ay)*(Px-Ax)` multiplies numbers of order `1e200` together, producing
   intermediate products of order `1e400`, which overflows float64's ~`1.8e308` maximum to `inf`;
   a second such computation involving a subtraction of two `inf` values can produce `nan`.
3. A natural, reasonable implementation of the side test (`if cross > 0: ... elif cross < 0: ...`)
   has no branch for `nan`, since `nan > 0` and `nan < 0` are both `False`. A conscientious
   implementer, aware that "this point already failed the on-line check so it must be strictly
   one side or the other," might add a defensive `else: raise AssertionError(...)` — a completely
   reasonable, common pattern for an "impossible" branch.
4. That `AssertionError` (or an `IndexError`, `KeyError`, or similar, depending on how the
   "impossible" branch is written) propagates out of `process_request` uncaught, because
   `design.md` never mandates a catch-all boundary — only that one exists as an outcome.
5. The spec requires `ValueError`, or a valid result. Neither occurs. This is precisely the
   failure mode the assignment's robustness requirement is written to prevent, and it is reachable
   from a legal, non-negative, finite, structurally-valid input.

### 4. Proposed design change

Add an explicit architectural rule to the Error-handling design section (not merely a stated
outcome): *`process_request`'s outermost frame must wrap the entire validate-then-scan pipeline in
a single catch-all boundary — any exception type other than the `ValueError` instances
intentionally raised by the validation layer must be caught and re-raised as `ValueError`.* This
is a specific, testable architectural mandate that makes F8's accepted risk survivable: geometry
is still allowed to produce numerically meaningless results under extreme input (the disclosed
residual risk stands), but it can no longer crash the process, which is the actual guarantee the
spec demands. This does not reopen F8's decision (no intermediate finiteness *checks* are added)
— it only closes the separate gap that F8's acceptance never addressed.

### 5. Impact on tests

The Testability section's "totality/exception containment" category currently only mentions "a
malformed point that would otherwise throw `TypeError`." It must be extended with a dedicated
case using deliberately extreme-but-legal-magnitude coordinates (structurally valid, non-negative,
finite) specifically designed to exercise the overflow path this objection describes, asserting
only `ValueError` or a valid result is ever observed — never a crash.

### 6. Severity

**Critical** — this is the one objection that directly threatens the assignment's single
most-emphasized non-functional requirement, using an input the specification does not exclude,
and the design document currently provides no mechanism, only an assertion, that the requirement
holds.

---

## What could pass all tests and still be broken in production?

**Risk: pure-Python per-point overhead makes a "correct, O(n)" implementation too slow for
NoTraffic's actual edge-deployment context.**
*Why tests might miss it:* `design.md` itself explicitly rules out a strict timing assertion in
the large-trajectory test ("not a strict timing assertion"), so a functionally correct but
unoptimized implementation (e.g. re-allocating tuples per point, redundant square roots) would
pass every unit test while being unacceptable in a real-time, on-device traffic system — which is
literally NoTraffic's product context, not a generic concern.
*How to expose it before shipping:* a separate, explicitly-labeled non-blocking benchmark (not a
pass/fail unit test) run against a 100,000-point synthetic trajectory, reviewed by eye rather than
asserted on, to catch orders-of-magnitude regressions without introducing test flakiness.

**Risk: silent misclassification (not a crash) under the same extreme-magnitude conditions as
Objection 3, if the "impossible" branch defaults to a value instead of raising.**
*Why tests might miss it:* if an implementer's defensive `else` branch quietly defaults to
"on-line" or "side A" instead of raising, `process_request` never crashes and never raises — it
returns a syntactically valid `RLRResult` with a semantically meaningless `crossing_timestamp`
(or an incorrect `None`). A test suite built only from the 8 worked examples plus "normal-range"
constructed cases would have no reason to probe this, since the output *type* is correct.
*How to expose it before shipping:* a property-style check — for a battery of extreme-magnitude
but legal inputs, confirm the reported side/on-line classification of each point is self-
consistent with an independently-computed reference (e.g. using Python's `decimal` or `fractions`
for the same points) rather than only checking that *a* result was returned.

**Risk: a spec-legal trajectory where the transition happens at the very first or very last
sample exposes an off-by-one in the boundary-tracking loop.**
*Why tests might miss it:* every one of the 8 worked examples has the transition somewhere in the
*interior* of a short trajectory; none tests a transition at trajectory index 0 or index n-1. A
loop that assumes "there is always a next/previous sample to compare against" is easy to write
correctly for interior transitions and easy to get wrong at the array's edges.
*How to expose it before shipping:* a dedicated constructed test with the minimum viable
trajectory (exactly two points, one on each strict side, no interior points at all) and a
constructed test where the transition is the very last pair of samples in a longer trajectory.

---

## Hidden tests I would expect

- A **vertical stop-line** worked-example-style scenario — none of the 8 given examples are
  vertical, despite the spec explicitly calling this out as a mandatory-support case; this is the
  single most obvious gap between "passes the 8 examples" and "actually implements the spec."
- A sample at **exactly** 1.0px from the segment (not 0.99 or 1.01), to check the `≤` inclusivity
  and interaction with the F7 epsilon in both directions.
- An **interpolated** crossing landing exactly at, or a hair inside/outside, the Finding-1 capsule
  boundary near an endpoint — distinguishing a careful implementation from one that reused the
  wrong tolerance (segment-only vs. capsule) inconsistently between sampled and interpolated cases.
- A malformed stop-line with endpoints that are **extremely close but not identical** (e.g.
  `1e-10` apart) — testing whether "exact equality" (F5) is actually implemented literally, or
  whether some other part of the code accidentally introduces tolerance.
- **Three or more** on-line samples in one trajectory (not just Example 8's exactly-two case) —
  directly targets Objection 1.
- A trajectory whose transition sits at the very **first or last** sample pair — targets the
  off-by-one risk noted above.
- A trajectory with **exactly two points**, one on each strict side — the minimum viable
  interpolation case, likely to expose loop-boundary assumptions.
- An extreme-magnitude but legal coordinate case — directly targets Objection 3.

---

## Questions I would ask the candidate

1. Walk me through exactly what your scan does if a trajectory has three samples within 1px of
   the stop-line instead of two — does it crash, hang, or silently produce a value before your
   validation layer rejects it?
2. You describe this as a "single pass," but your validation layer and your geometry scan are
   described as separate stages. Is this one pass over the data or two, and why does that
   distinction matter for a 100,000-point trajectory?
3. You accepted the risk that extreme-magnitude coordinates could overflow to `inf`/`NaN` during
   geometry computation instead of adding a defensive check. What specifically guarantees that
   can never surface as anything other than a `ValueError`?
4. Why does the 1-pixel tolerance apply identically to both sampled points and interpolated
   crossings, rather than keeping the interpolated case strict at the endpoints as your earlier
   assumption stated? What in the spec's wording actually forces that choice, versus merely
   permitting it?
5. If the guarantee that the trajectory changes side at most once were removed, what specifically
   in your single-pass state machine breaks first, and how would you detect that it broke?
6. Why is "side" computed from the infinite line while "on-line" is computed from the finite
   segment? Could one signed-distance-to-segment function serve both purposes, and would that
   change the result of any of the eight worked examples?
7. Your interpolation formula divides by the difference of two cross-products. Under what
   realistic circumstance, if any, could that denominator be zero or near-zero — does your design
   actually rule that out, or just assume it away?
8. If this needed to run in true O(1) memory against a live camera feed instead of a pre-collected
   trajectory list, which specific part of your design would have to change first?

---

# Reviewer verdict

**DESIGN CHANGES REQUIRED BEFORE TEST DESIGN**

Objection 3 leaves the assignment's single most heavily-emphasized requirement (total behavior —
`ValueError` or a valid result, nothing else) backed by an assertion rather than a specified
mechanism, and Objection 1 leaves Phase 3's own algorithm undefined on a plausible malformed
input that Phase 2's test matrix, as currently scoped, would not catch. Both must be resolved in
`design.md` before Phase 2 derives its test matrix from it, since a test matrix built from an
under-specified design will inherit its blind spots; Objection 2 is lower-stakes and can be fixed
in the same pass but would not by itself block moving forward.
