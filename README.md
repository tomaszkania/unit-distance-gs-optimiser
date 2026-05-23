# unit-distance-gs-optimiser

A typed Python verifier and parameter optimiser for Will Sawin's explicit lower
bound for the planar unit-distance problem.

The headline certificate verifies the rounded exponent

```text
delta = 0.03175083808192398
exponent = 1.031750838081924
```

within Sawin's Lemma 12 / Proposition 10 framework.  The improved certificate
uses the non-prefix ramified set

```text
T = (first 81 odd primes) \ {197, 337} ∪ {433, 601}
|S_Q| = 1278
#{p in S_Q : p splits in Q(sqrt(prod T))} = 240
R = 32.49523163513887
```

For comparison, the repository also keeps the earlier prefix-81 certificate,
which verifies exponent `1.0317221200362845`.

The intended public repository path is

```text
https://github.com/tomaszkania/unit-distance-gs-optimiser
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
unit-distance-gs verify certificates/t81-swap-197-337-to-433-601.json
```

Expected headline output:

```json
{
  "valid": true,
  "T_size": 81,
  "last_prime_in_T": 601,
  "selected_count": 1278,
  "split_count": 240,
  "capacity": 1518,
  "total_weight": 1518,
  "delta": 0.03175083808192398,
  "exponent": 1.031750838081924
}
```

## Notebook API

Install the optional notebook extra and open the demonstration notebook:

```bash
pip install -e ".[notebook]"
jupyter lab notebooks/verify_certificate.ipynb
```

The notebook also bootstraps `src/`, so it can run from a fresh clone before
installation.  The notebook-facing API is intentionally small and dependency-free:

```python
from pathlib import Path
from unit_distance_gs_optimiser.notebook import (
    exponent_markdown,
    load_certificate,
    load_certificate_summary,
    markdown_summary_table,
    search_t_summary,
)

certificate_path = Path("certificates/t81-swap-197-337-to-433-601.json")
summary = load_certificate_summary(certificate_path)
print(markdown_summary_table(summary))

# Re-run the optimiser for the same non-prefix T.
certificate = load_certificate(certificate_path)
found_summary = search_t_summary(certificate.t, prime_limit=200_000)
print(exponent_markdown(summary, found_summary))
```

## Command-line searches

Verify the improved stored certificate:

```bash
unit-distance-gs verify certificates/t81-swap-197-337-to-433-601.json
```

Re-run the prefix-81 optimisation:

```bash
unit-distance-gs search \
  --t-size 81 \
  --prime-limit 200000 \
  --name t81-first-odd-primes-exponent-1.031722120036 \
  --write-certificate certificates/t81-first-odd-primes.json
```

Re-run the optimisation for an explicit non-prefix `T` extracted from an
existing certificate:

```bash
unit-distance-gs search-t \
  --t-certificate certificates/t81-swap-197-337-to-433-601.json \
  --prime-limit 200000 \
  --name t81-swap-197-337-to-433-601-regenerated \
  --write-certificate certificates/t81-swap-197-337-to-433-601-regenerated.json
```

Run the heuristic swap search suggested by the splitting-pattern feedback:

```bash
unit-distance-gs swap-search \
  --t-size 81 \
  --prime-limit 200000 \
  --add-prime-limit 1300 \
  --steps 2 \
  --top-swaps 2 \
  --name t81-swap-search \
  --write-certificate certificates/t81-swap-search.json
```

The `swap-search` command ranks single swaps in `T` by a Legendre-symbol
heuristic: it favours swaps expected to turn valuable split primes into
non-split primes, thereby freeing Golod--Shafarevich budget, while penalising
increased discriminant.  Each accepted move is then checked by the full optimiser.
The stored certificate is still the authoritative object for verification.

## Method

The optimiser uses a Dinkelbach-style transformation.  For a trial `delta`, it
maximises `numerator - delta * denominator`; this makes the choice of `R` and the
choice of `k(p)` explicit, and leaves a two-weight knapsack problem for `S_Q`.
The final verifier evaluates Sawin's equation (11) with the `+1` in the
denominator included.

The non-prefix improvement changes the splitting pattern by replacing `197` and
`337` in `T` by `433` and `601`.  This reduces the number of selected split
primes from `254` to `240`; the freed budget lets the optimiser select `1278`
primes rather than `1264`.

## Tests

```bash
pytest
```

The test suite verifies the arithmetic helpers, both stored certificates, the
notebook-facing API, explicit-`T` optimisation, and a small swap-proposal
instance.

## Article

The article source is in `notes/sawin_parameter_optimisation.tex`.  It explains
the parameter improvement, the splitting-pattern engineering, and the limitations
of this kind of numerical sharpening.  A local TeX installation can compile it
with

```bash
make article
```
