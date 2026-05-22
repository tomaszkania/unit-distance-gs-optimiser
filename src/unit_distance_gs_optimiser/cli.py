"""Command-line interface for the Sawin parameter verifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .model import Certificate
from .notebook import certificate_summary
from .search import optimise_prefix


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
    """Run the ``search`` subcommand.

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
    if args.write_certificate is not None:
        output_path = Path(args.write_certificate)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        certificate.write_json(output_path)
    summary = certificate_summary(certificate)
    summary.update(
        {
            "search_prime_limit": result.prime_limit,
            "positivity_threshold": result.positivity_threshold,
            "candidate_limit_exceeds_threshold": result.prime_limit > result.positivity_threshold,
        }
    )
    print(json.dumps(summary, indent=2))
    return 0 if bool(summary["valid"]) else 1


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
    search_parser.add_argument("--name", type=str, default=None, help="certificate name")
    search_parser.add_argument(
        "--description", type=str, default="", help="certificate description"
    )
    search_parser.add_argument(
        "--write-certificate",
        type=Path,
        default=None,
        help="optional path for writing the generated certificate",
    )
    search_parser.set_defaults(func=search_command)
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
