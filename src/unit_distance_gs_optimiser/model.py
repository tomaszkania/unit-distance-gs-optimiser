"""Data models and verification formulas for Sawin's equation (11)."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .arithmetic import is_prime, legendre_symbol, quadratic_character_of_product


@dataclass(frozen=True, slots=True)
class Candidate:
    """A rational prime candidate for ``S_Q``.

    Parameters
    ----------
    p:
        Rational prime.
    e:
        Ramification index used in Sawin's formula.
    split:
        Whether ``p`` splits in ``Q = Q(sqrt(prod(T)))``.
    """

    p: int
    e: int
    split: bool

    @property
    def weight(self) -> int:
        """Return the Golod--Shafarevich budget weight."""

        return 2 if self.split else 1


@dataclass(frozen=True, slots=True)
class SelectedPrime:
    """A selected prime together with the exponent ``k(p)``.

    Parameters
    ----------
    p:
        Rational prime in ``S_Q``.
    k:
        Positive integer exponent attached to ``p``.
    """

    p: int
    k: int


@dataclass(frozen=True, slots=True)
class Certificate:
    """A parameter certificate for Sawin's equation (11).

    Parameters
    ----------
    name:
        Human-readable certificate name.
    t:
        Tuple representing the set ``T``.
    selected:
        Selected primes and their exponents.
    r:
        Real parameter ``R > 1``.
    description:
        Optional provenance text.
    """

    name: str
    t: tuple[int, ...]
    selected: tuple[SelectedPrime, ...]
    r: float
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise the certificate to a JSON-compatible dictionary.

        Returns
        -------
        dict[str, Any]
            JSON-compatible certificate.
        """

        return {
            "name": self.name,
            "description": self.description,
            "T": list(self.t),
            "R": self.r,
            "selected": [{"p": item.p, "k": item.k} for item in self.selected],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Certificate:
        """Construct a certificate from parsed JSON.

        Parameters
        ----------
        payload:
            Parsed JSON object.

        Returns
        -------
        Certificate
            Parsed certificate.
        """

        try:
            selected = tuple(
                SelectedPrime(p=int(item["p"]), k=int(item["k"]))
                for item in payload["selected"]
            )
            return cls(
                name=str(payload.get("name", "unnamed")),
                description=str(payload.get("description", "")),
                t=tuple(int(q) for q in payload["T"]),
                selected=selected,
                r=float(payload["R"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            msg = "invalid certificate payload"
            raise ValueError(msg) from exc

    def write_json(self, path: str | Path) -> None:
        """Write the certificate as pretty JSON.

        Parameters
        ----------
        path:
            Destination path.
        """

        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read_json(cls, path: str | Path) -> Certificate:
        """Read a certificate from JSON.

        Parameters
        ----------
        path:
            Path to the JSON certificate.

        Returns
        -------
        Certificate
            Parsed certificate.
        """

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            msg = "certificate JSON must be an object"
            raise ValueError(msg)
        return cls.from_dict(payload)


@dataclass(frozen=True, slots=True)
class EquationResult:
    """Numerical evaluation of Sawin's equation (11).

    Parameters
    ----------
    numerator:
        Numerator in equation (11).
    denominator:
        Denominator in equation (11), including the ``+1`` inside the logarithm.
    delta:
        Quotient ``numerator / denominator``.
    """

    numerator: float
    denominator: float
    delta: float

    @property
    def exponent(self) -> float:
        """Return ``1 + delta``."""

        return 1.0 + self.delta


@dataclass(frozen=True, slots=True)
class VerificationReport:
    """Verification output for a certificate.

    Parameters
    ----------
    valid:
        Whether all exact combinatorial checks passed.
    errors:
        Verification errors.
    equation:
        Numerical equation (11) evaluation.
    capacity:
        Golod--Shafarevich capacity from Sawin's condition (9).
    total_weight:
        ``|S_Q|`` plus the number of selected primes split in ``Q``.
    split_count:
        Number of selected primes split in ``Q``.
    selected_count:
        Number of selected primes.
    max_selected_prime:
        Largest selected prime, or ``None`` when ``S_Q`` is empty.
    """

    valid: bool
    errors: tuple[str, ...]
    equation: EquationResult
    capacity: int
    total_weight: int
    split_count: int
    selected_count: int
    max_selected_prime: int | None


def golod_shafarevich_capacity(t: Sequence[int]) -> int:
    """Return the budget allowed by Sawin's condition (9).

    Parameters
    ----------
    t:
        The set ``T``.

    Returns
    -------
    int
        Maximum value of ``|S_Q| + #{split primes}``.
    """

    t_size = len(t)
    return math.floor(((t_size - 1) ** 2) / 4.0 - t_size - 1)


def count_three_mod_four(t: Sequence[int]) -> int:
    """Count elements of ``T`` congruent to ``3`` modulo ``4``.

    Parameters
    ----------
    t:
        The set ``T``.

    Returns
    -------
    int
        Count of primes congruent to ``3`` modulo ``4``.
    """

    return sum(1 for q in t if q % 4 == 3)


def ramification_index(p: int, t: Sequence[int]) -> int:
    """Return the ramification index ``e(p)`` used in Lemma 12.

    Parameters
    ----------
    p:
        Rational prime.
    t:
        The set ``T``.

    Returns
    -------
    int
        ``2`` if ``p`` is ``2`` or belongs to ``T``; otherwise ``1``.
    """

    return 2 if p == 2 or p in set(t) else 1


def splits_in_quadratic_field_q(p: int, t: Sequence[int]) -> bool:
    """Check whether ``p`` splits in ``Q(sqrt(prod(T)))``.

    Ramified primes are not counted as split for Sawin's condition (9).

    Parameters
    ----------
    p:
        Rational prime.
    t:
        The set ``T``.

    Returns
    -------
    bool
        Whether ``p`` is unramified and split in the quadratic field.
    """

    if p == 2 or p in set(t):
        return False
    if not is_prime(p):
        msg = "p must be prime"
        raise ValueError(msg)
    return quadratic_character_of_product(t, p) == 1


def is_admissible_for_s_q(p: int, t: Sequence[int]) -> bool:
    """Check Sawin's local condition for membership in ``S_Q``.

    The condition is that ``p`` is congruent to ``1`` modulo ``4`` or is inert
    in ``Q(sqrt(q))`` for at least one ``q`` in ``T``.  For ``p = 2`` this is
    implemented by the elementary criterion ``q == 5 mod 8``.

    Parameters
    ----------
    p:
        Rational prime.
    t:
        The set ``T``.

    Returns
    -------
    bool
        Whether ``p`` may be included in ``S_Q``.
    """

    if p == 2:
        return any(q % 8 == 5 for q in t)
    if p % 4 == 1:
        return True
    return any(q != p and legendre_symbol(q, p) == -1 for q in t)


def candidate_from_prime(p: int, t: Sequence[int]) -> Candidate:
    """Build a candidate record from a prime.

    Parameters
    ----------
    p:
        Rational prime.
    t:
        The set ``T``.

    Returns
    -------
    Candidate
        Candidate with ramification and splitting data.
    """

    return Candidate(p=p, e=ramification_index(p, t), split=splits_in_quadratic_field_q(p, t))


def build_candidates(t: Sequence[int], prime_limit: int) -> list[Candidate]:
    """Build all admissible candidates up to ``prime_limit``.

    Parameters
    ----------
    t:
        The set ``T``.
    prime_limit:
        Candidate prime bound.

    Returns
    -------
    list[Candidate]
        Admissible candidates sorted by prime.
    """

    from .arithmetic import primes_up_to

    return [
        candidate_from_prime(p, t)
        for p in primes_up_to(prime_limit)
        if is_admissible_for_s_q(p, t)
    ]


def constant_term(t: Sequence[int]) -> float:
    """Return the numerator terms independent of ``S_Q`` and ``R``.

    Parameters
    ----------
    t:
        The set ``T``.

    Returns
    -------
    float
        Constant term in the numerator of Sawin's equation (11).
    """

    log_lambda_squared = math.log(4.0) + sum(math.log(q) for q in t)
    return (
        0.5 * math.log(2.0 * math.pi / math.e)
        - 0.125 * log_lambda_squared
        - 0.5 * math.log(log_lambda_squared / 2.0)
    )


def _log_exp_plus_one(x: float) -> float:
    """Return ``log(exp(x) + 1)`` stably.

    Parameters
    ----------
    x:
        Real input.

    Returns
    -------
    float
        Stable value of ``log(exp(x) + 1)``.
    """

    if x > 50.0:
        return x + math.log1p(math.exp(-x))
    return math.log1p(math.exp(x))


def evaluate_equation_11(
    t: Sequence[int], selected: Sequence[SelectedPrime], r: float
) -> EquationResult:
    """Evaluate Sawin's equation (11).

    Parameters
    ----------
    t:
        The set ``T``.
    selected:
        Selected primes and exponents ``k(p)``.
    r:
        Real parameter ``R > 1``.

    Returns
    -------
    EquationResult
        Numerator, denominator and quotient ``delta``.
    """

    if r <= 1.0:
        msg = "R must be greater than 1"
        raise ValueError(msg)
    numerator = math.log1p(-1.0 / r) + constant_term(t)
    denominator_log_product = math.log(2.0 * r)
    for item in selected:
        candidate = candidate_from_prime(item.p, t)
        numerator += math.log(item.k + 1.0) / (4.0 * candidate.e)
        denominator_log_product += item.k * math.log(item.p) / (2.0 * candidate.e)
    denominator = _log_exp_plus_one(denominator_log_product)
    return EquationResult(numerator=numerator, denominator=denominator, delta=numerator / denominator)


def verify_certificate(certificate: Certificate) -> VerificationReport:
    """Verify exact conditions and evaluate equation (11).

    Parameters
    ----------
    certificate:
        Certificate to verify.

    Returns
    -------
    VerificationReport
        Exact verification status and numerical exponent.
    """

    errors: list[str] = []
    t = certificate.t
    selected = certificate.selected

    if not t:
        errors.append("T must be non-empty")
    if len(set(t)) != len(t):
        errors.append("T contains duplicate primes")
    for q in t:
        if q == 2 or not is_prime(q):
            errors.append(f"T contains a non-odd-prime: {q}")
    if count_three_mod_four(t) % 2 != 1:
        errors.append("the number of elements of T congruent to 3 modulo 4 is not odd")

    selected_primes = [item.p for item in selected]
    if len(set(selected_primes)) != len(selected_primes):
        errors.append("S_Q contains duplicate primes")
    if any(item.k <= 0 for item in selected):
        errors.append("all k(p) must be positive")
    for item in selected:
        if not is_prime(item.p):
            errors.append(f"S_Q contains a non-prime: {item.p}")
            continue
        if not is_admissible_for_s_q(item.p, t):
            errors.append(f"prime {item.p} fails Sawin's local admissibility condition")

    split_count = 0
    total_weight = 0
    for item in selected:
        if is_prime(item.p):
            split = splits_in_quadratic_field_q(item.p, t)
            split_count += int(split)
            total_weight += 2 if split else 1

    capacity = golod_shafarevich_capacity(t)
    if total_weight > capacity:
        errors.append(f"Golod--Shafarevich budget exceeded: {total_weight} > {capacity}")

    try:
        equation = evaluate_equation_11(t, selected, certificate.r)
    except ValueError as exc:
        errors.append(str(exc))
        equation = EquationResult(numerator=float("nan"), denominator=float("nan"), delta=float("nan"))

    return VerificationReport(
        valid=not errors,
        errors=tuple(errors),
        equation=equation,
        capacity=capacity,
        total_weight=total_weight,
        split_count=split_count,
        selected_count=len(selected),
        max_selected_prime=max(selected_primes) if selected_primes else None,
    )
