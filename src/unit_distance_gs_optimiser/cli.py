"""Command-line interface for the Sawin parameter verifier."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .model import Certificate
from .notebook import certificate_summary
from .search import optimise_prefix, optimise_t, swap_search


def parse_prime_list(raw: str) -> tuple[int, ...]:
    """Parse a comma-separated list of primes.

    Parameters
    ----------
    raw:
        Comma-separated integer list.

    Returns
    -------
    tuple[int, ...]
        Parsed integers, sorted increasingly.
    """

    try:
        return tuple(sorted({int(part.strip()) for part in raw.split(",") if part.strip()}))
    except ValueError as exc:
        msg = "expected a comma-separated list of integers"
        raise argparse.ArgumentTypeError(msg) from exc


def certificate_t(path: Path) -> tuple[int, ...]:
    """Read ``T`` from a certificate file.

    Parameters
    ----------
    path:
        Certificate path.

    Returns
    -------
    tuple[int, ...]
        Ramified prime set from the certificate.
    """

    return Certificate.read_json(path).t


def write_certificate_if_requested(certificate: Certificate, output_path: Path | None) -> None:
    """Write a certificate when an output path was supplied.

    Parameters
    ----------
    certificate:
        Certificate to write.
    output_path:
        Optional destination path.
    """

    if output_path is None:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    certificate.write_json(output_path)


def search_summary_payload(certificate: Certificate, prime_limit: int, threshold: float) -> dict[str, object]:
    """Build the common CLI JSON payload for search commands.

    Parameters
    ----------
    certificate:
        Certificate to summarise.
    prime_limit:
        Candidate prime limit used by the search.
    threshold:
        Positivity threshold computed from the final delta.

    Returns
    -------
    dict[str, object]
        JSON-serialisable summary.
    """

    summary = certificate_summary(certificate)
    summary.update(
        {
            "search_prime_limit": prime_limit,
            "positivity_threshold": threshold,
            "candidate_limit_exceeds_threshold": prime_limit > threshold,
        }
    )
    return summary


def verify_command(args: argparse.Namespace) -> int:
    """Run the ``verify`` subcommand.

    Parameters
    ----------
    args:
        Parsed command-line arguments.

    Returns
    -------
    int
        Process exit code.
    """

    certificate = Certificate.read_json(args.certificate)
    summary = certificate_summary(certificate)
    print(json.dumps(summary, indent=2))
    return 0 if bool(summary["valid"]) else 1


def search_command(args: argparse.Namespace) -> int:
    """Run the prefix-``T`` ``search`` subcommand.

    Parameters
    ----------
    args:
        Parsed command-line arguments.

    Returns
    -------
    int
        Process exit code.
    """

    result = optimise_prefix(
        t_size=args.t_size,
        prime_limit=args.prime_limit,
        name=args.name,
        description=args.description,
    )
    certificate = result.certificate
    write_certificate_if_requested(certificate, args.write_certificate)
    summary = search_summary_payload(certificate, result.prime_limit, result.positivity_threshold)
    print(json.dumps(summary, indent=2))
    return 0 if bool(summary["valid"]) else 1


def explicit_t_from_args(args: argparse.Namespace) -> tuple[int, ...]:
    """Extract an explicit ``T`` from parsed command-line arguments.

    Parameters
    ----------
    args:
        Parsed arguments with ``t`` and ``t_certificate`` attributes.

    Returns
    -------
    tuple[int, ...]
        Explicit ramified prime set.
    """

    provided = [args.t is not None, args.t_certificate is not None]
    if sum(provided) != 1:
        msg = "exactly one of --t or --t-certificate is required"
        raise ValueError(msg)
    if args.t is not None:
        return args.t
    return certificate_t(args.t_certificate)


def search_t_command(args: argparse.Namespace) -> int:
    """Run the explicit-``T`` search subcommand.

    Parameters
    ----------
    args:
        Parsed command-line arguments.

    Returns
    -------
    int
        Process exit code.
    """

    try:
        t = explicit_t_from_args(args)
    except ValueError as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        return 2
    result = optimise_t(
        t,
        prime_limit=args.prime_limit,
        name=args.name,
        description=args.description,
    )
    certificate = result.certificate
    write_certificate_if_requested(certificate, args.write_certificate)
    summary = search_summary_payload(certificate, result.prime_limit, result.positivity_threshold)
    print(json.dumps(summary, indent=2))
    return 0 if bool(summary["valid"]) else 1


def optional_initial_t(args: argparse.Namespace) -> Sequence[int] | None:
    """Read the optional starting ``T`` for the swap search.

    Parameters
    ----------
    args:
        Parsed command-line arguments.

    Returns
    -------
    Sequence[int] | None
        Explicit starting ``T`` or ``None`` for the prefix default.
    """

    provided = [args.initial_t is not None, args.initial_t_certificate is not None]
    if sum(provided) > 1:
        msg = "at most one of --initial-t and --initial-t-certificate may be supplied"
        raise ValueError(msg)
    if args.initial_t is not None:
        return args.initial_t
    if args.initial_t_certificate is not None:
        return certificate_t(args.initial_t_certificate)
    return None


def swap_search_command(args: argparse.Namespace) -> int:
    """Run the heuristic-guided swap search subcommand.

    Parameters
    ----------
    args:
        Parsed command-line arguments.

    Returns
    -------
    int
        Process exit code.
    """

    try:
        initial_t = optional_initial_t(args)
    except ValueError as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        return 2

    result = swap_search(
        initial_t=initial_t,
        t_size=args.t_size,
        prime_limit=args.prime_limit,
        add_prime_limit=args.add_prime_limit,
        steps=args.steps,
        top_swaps=args.top_swaps,
        target_split_count=args.target_split_count,
        preserve_residue_mod_four=not args.allow_mod_four_change,
        name=args.name,
    )
    certificate = result.best.certificate
    write_certificate_if_requested(certificate, args.write_certificate)
    summary = search_summary_payload(certificate, result.best.prime_limit, result.best.positivity_threshold)
    summary.update(
        {
            "evaluated_moves": result.evaluated_moves,
            "accepted_swaps": [
                {
                    "drop": step.move.drop,
                    "add": step.move.add,
                    "heuristic_score": step.move.heuristic_score,
                    "previous_delta": step.previous_delta,
                    "new_delta": step.new_delta,
                }
                for step in result.steps
            ],
        }
    )
    print(json.dumps(summary, indent=2))
    return 0 if bool(summary["valid"]) else 1


def add_common_search_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common name/description/output arguments to a search parser.

    Parameters
    ----------
    parser:
        Parser to mutate.
    """

    parser.add_argument("--name", type=str, default=None, help="certificate name")
    parser.add_argument("--description", type=str, default="", help="certificate description")
    parser.add_argument(
        "--write-certificate",
        type=Path,
        default=None,
        help="optional path for writing the generated certificate",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser.
    """

    parser = argparse.ArgumentParser(
        prog="unit-distance-gs",
        description="Verify and search Sawin-style unit-distance parameter certificates.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify", help="verify a JSON certificate")
    verify_parser.add_argument("certificate", type=Path, help="path to certificate JSON")
    verify_parser.set_defaults(func=verify_command)

    search_parser = subparsers.add_parser("search", help="run a prefix-T parameter search")
    search_parser.add_argument("--t-size", type=int, default=81, help="number of odd primes in T")
    search_parser.add_argument(
        "--prime-limit",
        type=int,
        default=200_000,
        help="candidate prime search limit",
    )
    add_common_search_arguments(search_parser)
    search_parser.set_defaults(func=search_command)

    search_t_parser = subparsers.add_parser("search-t", help="run a search for an explicit T")
    search_t_parser.add_argument("--t", type=parse_prime_list, default=None, help="comma list for T")
    search_t_parser.add_argument(
        "--t-certificate",
        type=Path,
        default=None,
        help="read T from an existing certificate",
    )
    search_t_parser.add_argument(
        "--prime-limit",
        type=int,
        default=200_000,
        help="candidate prime search limit",
    )
    add_common_search_arguments(search_t_parser)
    search_t_parser.set_defaults(func=search_t_command)

    swap_parser = subparsers.add_parser("swap-search", help="run a heuristic non-prefix T search")
    swap_parser.add_argument(
        "--initial-t", type=parse_prime_list, default=None, help="optional comma list for starting T"
    )
    swap_parser.add_argument(
        "--initial-t-certificate",
        type=Path,
        default=None,
        help="read starting T from an existing certificate",
    )
    swap_parser.add_argument(
        "--t-size", type=int, default=81, help="prefix size when no explicit starting T is given"
    )
    swap_parser.add_argument(
        "--prime-limit",
        type=int,
        default=200_000,
        help="candidate prime search limit for each exact optimisation",
    )
    swap_parser.add_argument(
        "--add-prime-limit",
        type=int,
        default=1_300,
        help="upper bound for primes that may be swapped into T",
    )
    swap_parser.add_argument("--steps", type=int, default=2, help="maximum accepted greedy steps")
    swap_parser.add_argument(
        "--top-swaps",
        type=int,
        default=2,
        help="heuristic proposals optimised exactly at each step",
    )
    swap_parser.add_argument(
        "--target-split-count",
        type=int,
        default=150,
        help="number of valuable split primes used in the heuristic",
    )
    swap_parser.add_argument(
        "--allow-mod-four-change",
        action="store_true",
        help="allow swaps that change the residue class modulo 4",
    )
    add_common_search_arguments(swap_parser)
    swap_parser.set_defaults(func=swap_search_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point.

    Parameters
    ----------
    argv:
        Optional argument list.  When ``None``, ``argparse`` reads from ``sys.argv``.

    Returns
    -------
    int
        Process exit code.
    """

    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
