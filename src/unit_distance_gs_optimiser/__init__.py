"""Verifier and optimiser for Sawin-style unit-distance lower bounds."""

from .model import Certificate, EquationResult, SelectedPrime, VerificationReport, verify_certificate
from .notebook import (
    certificate_summary,
    exponent_markdown,
    load_certificate_summary,
    markdown_summary_table,
    report_summary,
    search_prefix_summary,
)
from .search import SearchResult, optimise_prefix

__all__ = [
    "Certificate",
    "EquationResult",
    "SearchResult",
    "SelectedPrime",
    "VerificationReport",
    "certificate_summary",
    "exponent_markdown",
    "load_certificate_summary",
    "markdown_summary_table",
    "optimise_prefix",
    "report_summary",
    "search_prefix_summary",
    "verify_certificate",
]
