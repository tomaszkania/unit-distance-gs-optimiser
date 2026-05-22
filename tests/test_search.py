"""Tests for the optimiser."""

from __future__ import annotations

from unit_distance_gs_optimiser.model import Candidate, verify_certificate
from unit_distance_gs_optimiser.search import best_k_score, optimise_prefix


def test_best_k_score_is_positive_for_small_prime_near_certificate_delta() -> None:
    """The local optimiser chooses a positive exponent for p = 2."""

    score, k = best_k_score(Candidate(p=2, e=2, split=False), 0.03172)
    assert score > 0
    assert k > 1


def test_small_search_returns_a_well_formed_certificate() -> None:
    """A small search produces a syntactically valid certificate when parity permits."""

    result = optimise_prefix(t_size=13, prime_limit=1_000)
    report = verify_certificate(result.certificate)
    assert report.valid
    assert report.selected_count > 0
