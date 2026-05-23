"""Tests for the optimiser."""

from __future__ import annotations

from pathlib import Path

from unit_distance_gs_optimiser.model import Candidate, Certificate, verify_certificate
from unit_distance_gs_optimiser.search import (
    apply_swap,
    best_k_score,
    optimise_prefix,
    optimise_t,
    propose_swaps,
)


ROOT = Path(__file__).resolve().parents[1]
SWAP_CERTIFICATE = ROOT / "certificates" / "t81-swap-197-337-to-433-601.json"


def test_best_k_score_is_positive_for_small_prime_near_certificate_delta() -> None:
    """The local optimiser chooses a positive exponent for p = 2."""

    score, k = best_k_score(Candidate(p=2, e=2, split=False), 0.03175)
    assert score > 0
    assert k > 1


def test_small_search_returns_a_well_formed_certificate() -> None:
    """A small search produces a syntactically valid certificate when parity permits."""

    result = optimise_prefix(t_size=13, prime_limit=1_000)
    report = verify_certificate(result.certificate)
    assert report.valid
    assert report.selected_count > 0


def test_optimise_t_accepts_non_prefix_t() -> None:
    """The explicit-T optimiser accepts the improved non-prefix ramified set."""

    certificate = Certificate.read_json(SWAP_CERTIFICATE)
    result = optimise_t(certificate.t, prime_limit=20_000)
    report = verify_certificate(result.certificate)
    assert report.valid
    assert report.equation.exponent > 1.0317


def test_propose_and_apply_swaps() -> None:
    """The swap proposal machinery returns legal single swaps."""

    result = optimise_prefix(t_size=13, prime_limit=1_000)
    report = verify_certificate(result.certificate)
    moves = propose_swaps(
        result.certificate.t,
        result.certificate.selected,
        report.equation.delta,
        add_prime_limit=100,
        target_split_count=10,
    )
    assert moves
    new_t = apply_swap(result.certificate.t, moves[0])
    assert moves[0].drop not in new_t
    assert moves[0].add in new_t
    assert len(new_t) == len(result.certificate.t)
