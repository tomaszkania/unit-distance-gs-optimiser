"""Finite-dimensional parameter search for Sawin's equation (11)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .arithmetic import first_odd_primes
from .model import (
    Candidate,
    Certificate,
    SelectedPrime,
    build_candidates,
    constant_term,
    evaluate_equation_11,
    golod_shafarevich_capacity,
)


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Output of a parameter search.

    Parameters
    ----------
    certificate:
        Certificate produced by the search.
    approximate_delta:
        Dinkelbach root obtained using the separable denominator approximation.
    positivity_threshold:
        Prime threshold above which the ``k = 1`` local score is non-positive.
    prime_limit:
        Candidate prime limit used in the search.
    """

    certificate: Certificate
    approximate_delta: float
    positivity_threshold: float
    prime_limit: int


def best_k_score(candidate: Candidate, delta: float) -> tuple[float, int]:
    """Maximise the local score over positive integers ``k``.

    Parameters
    ----------
    candidate:
        Candidate prime with ramification data.
    delta:
        Trial exponent increment.

    Returns
    -------
    tuple[float, int]
        Maximum score and a positive integer attaining it.
    """

    if delta <= 0.0:
        msg = "delta must be positive"
        raise ValueError(msg)
    log_p = math.log(candidate.p)
    continuous_stationary = 1.0 / (2.0 * delta * log_p) - 1.0
    k0 = max(1, math.floor(continuous_stationary))
    trial_ks = {1, k0 - 2, k0 - 1, k0, k0 + 1, k0 + 2, k0 + 3}
    best_score = -math.inf
    best_k = 1
    for k in trial_ks:
        if k < 1:
            continue
        score = math.log(k + 1.0) / (4.0 * candidate.e) - (
            delta * k * log_p / (2.0 * candidate.e)
        )
        if score > best_score:
            best_score = score
            best_k = k
    return best_score, best_k


def select_primes(
    candidates: Sequence[Candidate], t: Sequence[int], delta: float
) -> tuple[float, list[SelectedPrime]]:
    """Select ``S_Q`` for a fixed trial value of ``delta``.

    Parameters
    ----------
    candidates:
        Candidate rational primes.
    t:
        The set ``T``.
    delta:
        Trial exponent increment.

    Returns
    -------
    tuple[float, list[SelectedPrime]]
        Best separable objective contribution and selected primes.
    """

    capacity = golod_shafarevich_capacity(t)
    weight_one: list[tuple[float, SelectedPrime]] = []
    weight_two: list[tuple[float, SelectedPrime]] = []
    for candidate in candidates:
        score, k = best_k_score(candidate, delta)
        if score <= 0.0:
            continue
        item = (score, SelectedPrime(p=candidate.p, k=k))
        if candidate.weight == 1:
            weight_one.append(item)
        else:
            weight_two.append(item)

    weight_one.sort(key=lambda pair: pair[0], reverse=True)
    weight_two.sort(key=lambda pair: pair[0], reverse=True)

    prefix_one = [0.0]
    for score, _ in weight_one:
        prefix_one.append(prefix_one[-1] + score)
    prefix_two = [0.0]
    for score, _ in weight_two:
        prefix_two.append(prefix_two[-1] + score)

    best_value = -math.inf
    best_i = 0
    best_j = 0
    for j in range(min(len(weight_two), capacity // 2) + 1):
        i = min(len(weight_one), capacity - 2 * j)
        value = prefix_one[i] + prefix_two[j]
        if value > best_value:
            best_value = value
            best_i = i
            best_j = j

    selected = [item for _, item in weight_one[:best_i]] + [item for _, item in weight_two[:best_j]]
    selected.sort(key=lambda item: item.p)
    return best_value, selected


def dinkelbach_objective(
    candidates: Sequence[Candidate], t: Sequence[int], delta: float
) -> float:
    """Return the separable ``max(numerator - delta * denominator)`` objective.

    Parameters
    ----------
    candidates:
        Candidate rational primes.
    t:
        The set ``T``.
    delta:
        Trial exponent increment.

    Returns
    -------
    float
        Dinkelbach objective value.
    """

    r = 1.0 + 1.0 / delta
    r_term = math.log1p(-1.0 / r) - delta * math.log(2.0 * r)
    selected_value, _ = select_primes(candidates, t, delta)
    return constant_term(t) + r_term + selected_value


def solve_delta(
    candidates: Sequence[Candidate], t: Sequence[int], *, iterations: int = 60
) -> tuple[float, list[SelectedPrime]]:
    """Find the Dinkelbach root and associated selected primes.

    Parameters
    ----------
    candidates:
        Candidate rational primes.
    t:
        The set ``T``.
    iterations:
        Number of bisection iterations.

    Returns
    -------
    tuple[float, list[SelectedPrime]]
        Approximate root and selected primes.
    """

    lo = 1.0e-9
    hi = 0.1
    while dinkelbach_objective(candidates, t, hi) > 0.0:
        hi *= 2.0
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        if dinkelbach_objective(candidates, t, mid) > 0.0:
            lo = mid
        else:
            hi = mid
    _, selected = select_primes(candidates, t, lo)
    return lo, selected


def positivity_threshold(delta: float) -> float:
    """Return the threshold for a positive ``k = 1`` local score.

    Parameters
    ----------
    delta:
        Exponent increment.

    Returns
    -------
    float
        ``exp(log(2) / (2 delta))``.
    """

    return math.exp(math.log(2.0) / (2.0 * delta))


def optimise_prefix(
    t_size: int = 81,
    *,
    prime_limit: int = 200_000,
    name: str | None = None,
    description: str = "",
) -> SearchResult:
    """Optimise over candidates for ``T`` equal to the first odd primes.

    Parameters
    ----------
    t_size:
        Number of odd primes in ``T``.
    prime_limit:
        Upper bound for candidate primes in ``S_Q``.
    name:
        Optional certificate name.
    description:
        Optional certificate description.

    Returns
    -------
    SearchResult
        Search result and certificate.
    """

    t = tuple(first_odd_primes(t_size))
    candidates = build_candidates(t, prime_limit=prime_limit)
    approximate_delta, selected = solve_delta(candidates, t)
    r = 1.0 + 1.0 / approximate_delta
    exact_delta = evaluate_equation_11(t, selected, r).delta
    certificate = Certificate(
        name=name or f"first-{t_size}-odd-primes",
        t=t,
        selected=tuple(selected),
        r=r,
        description=description
        or (
            "Generated by the Dinkelbach-style optimiser. "
            f"The exact equation (11) value is delta={exact_delta:.15f}."
        ),
    )
    return SearchResult(
        certificate=certificate,
        approximate_delta=approximate_delta,
        positivity_threshold=positivity_threshold(exact_delta),
        prime_limit=prime_limit,
    )
