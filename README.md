# NoTraffic RLR Assignment (Part 1)

Detects the timestamp at which a vehicle's trajectory crosses a stop-line segment.

## Install / setup

Requires Python 3.10+ (developed and tested on 3.14). Standard library only - no
third-party packages to install.

1. Clone the repository and move into it:

   ```bash
   git clone https://github.com/brachaschushan/notraffic-rlr-take-home.git
   cd notraffic-rlr-take-home
   ```

2. (Optional but recommended) create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

3. No `pip install` step is required to run `main.py` or the tests - both are run directly
   from the repository root (see below) and the `rlr` package is imported from there.

   If you'd rather have `rlr` installed into the environment (e.g. to `import rlr` from
   outside this directory), install it in editable mode using the included
   `pyproject.toml`:

   ```bash
   pip install -e .
   ```

   This has no third-party dependencies to pull in - `dependencies = []` in
   `pyproject.toml` - it only registers the local `rlr` package.

## Run the worked-example driver

```bash
python main.py
```

Runs all 8 worked examples from the assignment plus two deliberately malformed requests,
printing each result (or the `ValueError` it raised) without aborting the run.

## Run the tests

```bash
python -m unittest
```

from the repository root. Uses only `unittest` from the standard library.

## Project layout

- `rlr/models.py` - `RLRRequest` / `RLRResult` dataclasses.
- `rlr/geometry.py` - point-to-segment distance, side classification, interpolation math.
- `rlr/validation.py` - malformed-input checks (no geometry).
- `rlr/processor.py` - `RLRRequestProcessor`, the single-pass crossing scan, and the
  total-processor exception boundary.
- `tests/test_rlr_processor.py` - the `unittest` suite.
- `main.py` - the worked-example / malformed-request driver.

## Assumptions beyond the specification

These are documented in detail (with the reasoning behind each) in `context.md` and
`design.md`; summarized here for quick reference:

- **Full trajectory validation.** The on-line-count rule ("more than one sample on the
  stop-line is malformed") requires scanning every point regardless of how quickly a
  crossing could otherwise be located, so `O(n)` work is unavoidable - the implementation
  does this in one interleaved pass, not two.
- **Interpolation targets the exact mathematical line**, not the ±1px tolerance band; only
  the resulting crossing *point* is then checked against the tolerance.
- **The 1px tolerance for a valid crossing applies identically to sampled points and to
  interpolated crossings**, including near a stop-line endpoint - a crossing up to 1px
  beyond an endpoint is valid. (This reverses an earlier, stricter reading; the spec's own
  wording ties the 1px tolerance to "the segment" wherever it defines a crossing.)
- **Timestamps must be finite, numeric, and non-`NaN`.** The spec's malformed-input list is
  framed in terms of coordinates; this extends the same numeric-validity requirement to
  timestamps for consistency with the total-processor guarantee.
- **Timestamp ordering and uniqueness are relied upon, not validated** - the spec states
  this may be assumed for Part 1.
- **No extra structural-type policing beyond what's required** - e.g. both `list` and
  `tuple` are accepted for points; no special-casing for `bool`-as-`int`.
- **A whitespace-only `car_id`** (e.g. `"   "`) is treated as empty and rejected.
- **Stop-line "identical endpoints" uses exact equality**, not a tolerance - the 1px
  tolerance is scoped to classifying trajectory points, not to detecting a degenerate
  stop-line.
- **No defensive check against numeric overflow in intermediate geometry values** (e.g. an
  extremely large-but-finite coordinate producing `inf`/`NaN` mid-computation). Input-level
  rejection of negative/`NaN`/infinite coordinates is relied upon instead; the residual risk
  is that such adversarial input could produce a numerically meaningless (but never
  crashing, and never a non-`ValueError`-exception-raising) result. See `critic.md`
  Objection 3 for why this doesn't threaten the total-processor guarantee: an explicit
  catch-all boundary in `RLRRequestProcessor.process_request` converts any unexpected
  exception into `ValueError`.
