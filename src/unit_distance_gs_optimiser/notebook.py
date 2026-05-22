"""Notebook-friendly API for certificate verification and parameter searches."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .model import Certificate, VerificationReport, verify_certificate
from .search import optimise_prefix


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

    return certificate_summary(Certificate.read_json(path))


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


def _required_real(summary: Mapping[str, object], key: str) -> float:
    """Read a required real-valued entry from a notebook summary.

    Parameters
    ----------
    summary:
        Summary mapping produced by this module.
    key:
        Required key.

    Returns
    -------
    float
        Numeric value converted to ``float``.

    Raises
    ------
    KeyError
        If ``key`` is absent.
    TypeError
        If the value is not an ``int`` or ``float``.
    """

    value = summary[key]
    if not isinstance(value, (int, float)):
        msg = f"summary[{key!r}] is not numeric"
        raise TypeError(msg)
    return float(value)


def exponent_markdown(summary: Mapping[str, object], *, title: str = "Resulting exponent") -> str:
    """Format the verified exponent as notebook Markdown.

    Parameters
    ----------
    summary:
        Summary produced by :func:`load_certificate_summary` or
        :func:`search_prefix_summary`.
    title:
        Markdown heading used at the top of the rendered block.

    Returns
    -------
    str
        Markdown block displaying ``delta`` and ``1 + delta``.
    """

    delta = _required_real(summary, "delta")
    exponent = _required_real(summary, "exponent")
    validity = summary.get("valid", "unknown")
    return (
        f"### {title}\n\n"
        f"Certificate valid: **{validity}**.\n\n"
        "The computed exponent increment is\n\n"
        f"\\[\\delta = {delta:.15f},\\qquad 1+\\delta = {exponent:.15f}.\\]\n\n"
        f"Rounded theorem exponent: **{exponent:.5f}**."
    )
