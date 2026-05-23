"""Tests for certificate verification."""

from __future__ import annotations

from pathlib import Path

from unit_distance_gs_optimiser.model import Certificate, verify_certificate


ROOT = Path(__file__).resolve().parents[1]
PREFIX_CERTIFICATE = ROOT / "certificates" / "t81-first-odd-primes.json"
SWAP_CERTIFICATE = ROOT / "certificates" / "t81-swap-197-337-to-433-601.json"


def test_prefix_t81_certificate_verifies() -> None:
    """The prefix certificate verifies the earlier advertised exponent."""

    certificate = Certificate.read_json(PREFIX_CERTIFICATE)
    report = verify_certificate(certificate)
    assert report.valid, report.errors
    assert report.capacity == 1518
    assert report.total_weight == 1518
    assert report.selected_count == 1264
    assert report.split_count == 254
    assert report.max_selected_prime == 16063
    assert report.equation.delta > 0.03172
    assert report.equation.exponent > 1.03172


def test_swap_t81_certificate_verifies() -> None:
    """The non-prefix swap certificate verifies the improved exponent."""

    certificate = Certificate.read_json(SWAP_CERTIFICATE)
    report = verify_certificate(certificate)
    assert report.valid, report.errors
    assert len(certificate.t) == 81
    assert 197 not in certificate.t
    assert 337 not in certificate.t
    assert 433 in certificate.t
    assert 601 in certificate.t
    assert report.capacity == 1518
    assert report.total_weight == 1518
    assert report.selected_count == 1278
    assert report.split_count == 240
    assert report.max_selected_prime == 16007
    assert report.equation.delta > 0.0317508
    assert report.equation.exponent > 1.0317508


def test_invalid_duplicate_selected_prime_is_detected() -> None:
    """A duplicate selected prime invalidates the certificate."""

    certificate = Certificate.read_json(SWAP_CERTIFICATE)
    duplicate = certificate.selected[0]
    bad = Certificate(
        name="bad",
        t=certificate.t,
        selected=certificate.selected + (duplicate,),
        r=certificate.r,
    )
    report = verify_certificate(bad)
    assert not report.valid
    assert any("duplicate" in error for error in report.errors)
