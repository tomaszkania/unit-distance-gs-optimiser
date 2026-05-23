"""Notebook-friendly API for certificate verification and parameter searches."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from .model import Certificate, VerificationReport, verify_certificate
from .search import optimise_prefix, optimise_t, swap_search


def report_summary(report: VerificationReport) -> dict[str, object]:
    """Convert a verification report to a notebook-friendly dictionary.

    Parameters
    ----------
    report:
        Verification report.

    Returns
    -------
    dict[str, object]
        Flat summary suitable for display in a notebook.
    """

    return {
        "valid": report.valid,
        "errors": list(report.errors),
        "capacity": report.capacity,
        "total_weight": report.total_weight,
        "selected_count": report.selected_count,
        "split_count": report.split_count,
        "max_selected_prime": report.max_selected_prime,
        "numerator": report.equation.numerator,
        "denominator": report.equation.denominator,
        "delta": report.equation.delta,
        "exponent": report.equation.exponent,
    }


def certificate_summary(certificate: Certificate) -> dict[str, object]:
    """Verify a certificate and return a flat summary dictionary.

    Parameters
    ----------
    certificate:
        Certificate to verify.

    Returns
    -------
    dict[str, object]
        Notebook-friendly certificate summary.
    """

    report = verify_certificate(certificate)
    summary = report_summary(report)
    summary.update(
        {
            "certificate_name": certificate.name,
            "T_size": len(certificate.t),
            "last_prime_in_T": certificate.t[-1] if certificate.t else None,
            "R": certificate.r,
        }
    )
    return summary


def load_certificate(path: str | Path) -> Certificate:
    """Load a JSON certificate for use in notebooks.

    Parameters
    ----------
    path:
        Path to a JSON certificate.

    Returns
    -------
    Certificate
        Parsed certificate.
    """

    return Certificate.read_json(path)


def load_certificate_summary(path: str | Path) -> dict[str, object]:
    """Load, verify and summarise a certificate.

    Parameters
    ----------
    path:
        Path to a JSON certificate.

    Returns
    -------
    dict[str, object]
        Notebook-friendly certificate summary.
    """

    return certificate_summary(load_certificate(path))


def search_prefix_summary(t_size: int = 81, *, prime_limit: int = 200_000) -> dict[str, object]:
    """Run a prefix-``T`` search and return a flat summary.

    Parameters
    ----------
    t_size:
        Number of odd primes in ``T``.
    prime_limit:
        Candidate prime search limit.

    Returns
    -------
    dict[str, object]
        Search and verification summary.
    """

    result = optimise_prefix(t_size=t_size, prime_limit=prime_limit)
    summary = certificate_summary(result.certificate)
    summary.update(
        {
            "search_prime_limit": result.prime_limit,
            "positivity_threshold": result.positivity_threshold,
            "candidate_limit_exceeds_threshold": result.prime_limit > result.positivity_threshold,
        }
    )
    return summary


def search_t_summary(t: Sequence[int], *, prime_limit: int = 200_000) -> dict[str, object]:
    """Run the optimiser for an explicit ``T`` and return a flat summary.

    Parameters
    ----------
    t:
        Explicit ramified prime set.
    prime_limit:
        Candidate prime search limit.

    Returns
    -------
    dict[str, object]
        Search and verification summary.
    """

    result = optimise_t(t, prime_limit=prime_limit)
    summary = certificate_summary(result.certificate)
    summary.update(
        {
            "search_prime_limit": result.prime_limit,
            "positivity_threshold": result.positivity_threshold,
            "candidate_limit_exceeds_threshold": result.prime_limit > result.positivity_threshold,
        }
    )
    return summary


def swap_search_summary(
    *,
    t_size: int = 81,
    prime_limit: int = 200_000,
    add_prime_limit: int = 1_300,
    steps: int = 2,
    top_swaps: int = 2,
) -> dict[str, object]:
    """Run the greedy swap search and return a notebook-friendly summary.

    Parameters
    ----------
    t_size:
        Size of the prefix starting set.
    prime_limit:
        Candidate prime search limit for each exact optimisation.
    add_prime_limit:
        Upper bound for primes that may be swapped into ``T``.
    steps:
        Maximum number of greedy accepted steps.
    top_swaps:
        Number of heuristic proposals optimised exactly at each step.

    Returns
    -------
    dict[str, object]
        Summary of the best certificate and accepted swaps.
    """

    result = swap_search(
        t_size=t_size,
        prime_limit=prime_limit,
        add_prime_limit=add_prime_limit,
        steps=steps,
        top_swaps=top_swaps,
    )
    summary = certificate_summary(result.best.certificate)
    summary.update(
        {
            "evaluated_moves": result.evaluated_moves,
            "accepted_swaps": [
                f"{step.move.drop} -> {step.move.add}" for step in result.steps
            ],
            "initial_delta": certificate_summary(result.initial.certificate)["delta"],
        }
    )
    return summary


def markdown_summary_table(summary: Mapping[str, object]) -> str:
    """Format a summary dictionary as a Markdown table.

    Parameters
    ----------
    summary:
        Summary mapping.

    Returns
    -------
    str
        Markdown table with ``key`` and ``value`` columns.
    """

    rows = ["| key | value |", "|---|---:|"]
    for key, value in summary.items():
        rows.append(f"| `{key}` | `{value}` |")
    return "\n".join(rows)


def exponent_markdown(
    verified_summary: Mapping[str, object], found_summary: Mapping[str, object] | None = None
) -> str:
    """Format the headline exponent in Markdown.

    Parameters
    ----------
    verified_summary:
        Summary for a stored certificate.
    found_summary:
        Optional summary produced by re-running a search.

    Returns
    -------
    str
        Markdown text displaying the verified and, when present, found exponent.
    """

    verified_exponent = float(verified_summary["exponent"])
    verified_delta = float(verified_summary["delta"])
    lines = [
        "### Headline exponent",
        "",
        f"Stored certificate: `delta = {verified_delta:.15f}`, ",
        f"so `1 + delta = {verified_exponent:.15f}`.",
    ]
    if found_summary is not None:
        found_exponent = float(found_summary["exponent"])
        found_delta = float(found_summary["delta"])
        lines.extend(
            [
                "",
                f"Re-run optimiser: `delta = {found_delta:.15f}`, ",
                f"so `1 + delta = {found_exponent:.15f}`.",
            ]
        )
    return "\n".join(lines)
