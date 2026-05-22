"""Tests for the notebook-facing API."""

from __future__ import annotations

from pathlib import Path

from unit_distance_gs_optimiser.notebook import (
    exponent_markdown,
    load_certificate_summary,
    markdown_summary_table,
)

ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE = ROOT / "certificates" / "t81-first-odd-primes.json"


def test_load_certificate_summary() -> None:
    """The notebook summary exposes the headline fields."""

    summary = load_certificate_summary(CERTIFICATE)
    assert summary["valid"] is True
    assert summary["T_size"] == 81
    assert summary["exponent"] > 1.03172


def test_markdown_summary_table() -> None:
    """The Markdown table helper formats mappings."""

    table = markdown_summary_table({"valid": True, "delta": 0.03172})
    assert "| key | value |" in table
    assert "`delta`" in table


def test_exponent_markdown() -> None:
    """The exponent helper renders the headline theorem exponent."""

    rendered = exponent_markdown({"valid": True, "delta": 0.03172212003628451, "exponent": 1.0317221200362845})
    assert "Resulting exponent" in rendered
    assert "1+\\delta = 1.031722120036284" in rendered
    assert "1.03172" in rendered
