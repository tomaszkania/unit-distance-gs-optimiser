"""Tests for the notebook-facing API."""

from __future__ import annotations

from pathlib import Path

from unit_distance_gs_optimiser.notebook import (
    exponent_markdown,
    load_certificate,
    load_certificate_summary,
    markdown_summary_table,
    search_t_summary,
)


ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE = ROOT / "certificates" / "t81-swap-197-337-to-433-601.json"


def test_load_certificate_summary() -> None:
    """The notebook summary exposes the headline fields."""

    summary = load_certificate_summary(CERTIFICATE)
    assert summary["valid"] is True
    assert summary["T_size"] == 81
    assert summary["exponent"] > 1.0317508


def test_search_t_summary() -> None:
    """The notebook API can re-optimise an explicit T from a certificate."""

    certificate = load_certificate(CERTIFICATE)
    summary = search_t_summary(certificate.t, prime_limit=20_000)
    assert summary["valid"] is True
    assert summary["T_size"] == 81
    assert summary["exponent"] > 1.0317


def test_markdown_summary_table() -> None:
    """The Markdown table helper formats mappings."""

    table = markdown_summary_table({"valid": True, "delta": 0.03175})
    assert "| key | value |" in table
    assert "`delta`" in table


def test_exponent_markdown() -> None:
    """The headline helper displays the verified exponent."""

    text = exponent_markdown({"delta": 0.031750838, "exponent": 1.031750838})
    assert "Headline exponent" in text
    assert "1.031750838" in text
