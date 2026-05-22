# unit-distance-gs-optimiser

Tomasz Kania tomasz.marcin.kania@gmail.com

A typed Python verifier and parameter optimiser for Will Sawin's explicit lower
bound for the planar unit-distance problem.

The stored certificate verifies the rounded exponent

```text
delta = 0.03172212003628451
exponent = 1.0317221200362845
```

within Sawin's Lemma 12 / Proposition 10 framework, using

```text
T = the first 81 odd primes = {3, 5, 7, ..., 421}
|S_Q| = 1264
#{p in S_Q : p splits in Q(sqrt(prod T))} = 254
R = 32.523744278634595
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
unit-distance-gs verify certificates/t81-first-odd-primes.json
```

Expected headline output:

```json
{
  "valid": true,
  "T_size": 81,
  "last_prime_in_T": 421,
  "selected_count": 1264,
  "split_count": 254,
  "capacity": 1518,
  "total_weight": 1518,
  "delta": 0.03172212003628451,
  "exponent": 1.0317221200362845
}
```

## Notebook API

The demonstration notebook now bootstraps the `src/` directory automatically, so it runs from a fresh clone in VS Code or Jupyter before an editable install.  The included `.vscode/settings.json` also tells Pylance where the package lives.

Open the notebook with:

```bash
jupyter lab notebooks/verify_certificate.ipynb
```

For a conventional editable install, use:

```bash
pip install -e ".[notebook]"
```

The notebook verifies the stored certificate and also re-runs the optimiser, displaying the resulting exponent found by the search.  The notebook-facing API is intentionally small and dependency-free:

```python
from pathlib import Path
from unit_distance_gs_optimiser.notebook import (
    exponent_markdown,
    load_certificate_summary,
    markdown_summary_table,
    search_prefix_summary,
)

summary = load_certificate_summary(Path("certificates/t81-first-odd-primes.json"))
print(markdown_summary_table(summary))
print(exponent_markdown(summary))

# Re-run the optimiser from a notebook.
search_summary = search_prefix_summary(t_size=81, prime_limit=200_000)
```

## Re-running the search

```bash
unit-distance-gs search \
  --t-size 81 \
  --prime-limit 200000 \
  --name t81-first-odd-primes-exponent-1.031722120036 \
  --write-certificate certificates/t81-first-odd-primes.json
```

The optimiser uses a Dinkelbach-style transformation.  For a trial `delta`, it
maximises `numerator - delta * denominator`; this makes the choice of `R` and the
choice of `k(p)` explicit, and leaves a two-weight knapsack problem for `S_Q`.
The final verifier evaluates Sawin's equation (11) with the `+1` in the
denominator included.

## Tests

```bash
pytest
```

The test suite verifies the arithmetic helpers, the stored certificate, the
notebook-facing API, and a small search instance.

## Article

The article source is in `notes/sawin_parameter_optimisation.tex`.  It uses
the supplied author/address block and explains the parameter improvement and
its limitations.  A local TeX installation can compile it with

```bash
make article
```
