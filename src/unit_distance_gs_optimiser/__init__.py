"""Verifier and optimiser for Sawin-style unit-distance lower bounds."""

from .model import Certificate, EquationResult, SelectedPrime, VerificationReport, verify_certificate
from .notebook import (
    certificate_summary,
    exponent_markdown,
    load_certificate,
    load_certificate_summary,
    markdown_summary_table,
    report_summary,
    search_prefix_summary,
    search_t_summary,
    swap_search_summary,
)
from .search import (
    SearchResult,
    SwapMove,
    SwapSearchResult,
    SwapStep,
    exact_delta,
    optimise_prefix,
    optimise_t,
    swap_search,
)

__all__ = [
    "Certificate",
    "EquationResult",
    "SearchResult",
    "SelectedPrime",
    "SwapMove",
    "SwapSearchResult",
    "SwapStep",
    "VerificationReport",
    "certificate_summary",
    "exact_delta",
    "exponent_markdown",
    "load_certificate",
    "load_certificate_summary",
    "markdown_summary_table",
    "optimise_prefix",
    "optimise_t",
    "report_summary",
    "search_prefix_summary",
    "search_t_summary",
    "swap_search",
    "swap_search_summary",
    "verify_certificate",
]
