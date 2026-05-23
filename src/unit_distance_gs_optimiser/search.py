"""Finite-dimensional parameter searches for Sawin's equation (11)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .arithmetic import first_odd_primes, legendre_symbol, primes_up_to
from .model import (
    Candidate,
    Certificate,
    SelectedPrime,
    build_candidates,
    constant_term,
    evaluate_equation_11,
    golod_shafarevich_capacity,
    splits_in_quadratic_field_q,
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


@dataclass(frozen=True, slots=True)
class SwapMove:
    """A proposed single swap in the ramified prime set ``T``.

    Parameters
    ----------
    drop:
        Prime removed from ``T``.
    add:
        Prime added to ``T``.
    heuristic_score:
        Splitting-pattern heuristic score used to rank the proposal.
    """

    drop: int
    add: int
    heuristic_score: float


@dataclass(frozen=True, slots=True)
class SwapStep:
    """One accepted greedy step in a swap search.

    Parameters
    ----------
    move:
        Accepted swap.
    previous_delta:
        Certified exponent increment before the swap.
    new_delta:
        Certified exponent increment after the swap.
    """

    move: SwapMove
    previous_delta: float
    new_delta: float


@dataclass(frozen=True, slots=True)
class SwapSearchResult:
    """Output of a heuristic-guided swap search.

    Parameters
    ----------
    initial:
        Optimisation result for the starting ``T``.
    best:
        Best optimisation result found.
    steps:
        Accepted greedy swap steps.
    evaluated_moves:
        Number of fully optimised swap proposals.
    """

    initial: SearchResult
    best: SearchResult
    steps: tuple[SwapStep, ...]
    evaluated_moves: int


@dataclass(frozen=True, slots=True)
class SplitTarget:
    """A selected split prime together with its local transformed value."""

    p: int
    score: float


def exact_delta(result: SearchResult) -> float:
    """Return the exact equation (11) delta of a search result.

    Parameters
    ----------
    result:
        Search result whose certificate should be evaluated.

    Returns
    -------
    float
        Verified value of Sawin's logarithmic quotient for the certificate.
    """

    certificate = result.certificate
    return evaluate_equation_11(certificate.t, certificate.selected, certificate.r).delta


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


def sorted_t(t: Sequence[int]) -> tuple[int, ...]:
    """Return ``T`` sorted as an immutable tuple.

    Parameters
    ----------
    t:
        Iterable representation of the ramified prime set.

    Returns
    -------
    tuple[int, ...]
        Increasing tuple of distinct entries.
    """

    return tuple(sorted(set(t)))


def optimise_t(
    t: Sequence[int],
    *,
    prime_limit: int = 200_000,
    name: str | None = None,
    description: str = "",
) -> SearchResult:
    """Optimise ``S_Q``, ``k`` and ``R`` for an explicit ``T``.

    Parameters
    ----------
    t:
        Explicit ramified prime set ``T``.
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

    t_tuple = sorted_t(t)
    candidates = build_candidates(t_tuple, prime_limit=prime_limit)
    approximate_delta, selected = solve_delta(candidates, t_tuple)
    r = 1.0 + 1.0 / approximate_delta
    exact = evaluate_equation_11(t_tuple, selected, r)
    certificate = Certificate(
        name=name or f"explicit-T-{len(t_tuple)}-exponent-{exact.exponent:.12f}",
        t=t_tuple,
        selected=tuple(selected),
        r=r,
        description=description
        or (
            "Generated by the Dinkelbach-style optimiser for an explicit T. "
            f"The exact equation (11) value is delta={exact.delta:.15f}."
        ),
    )
    return SearchResult(
        certificate=certificate,
        approximate_delta=approximate_delta,
        positivity_threshold=positivity_threshold(exact.delta),
        prime_limit=prime_limit,
    )


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
    return optimise_t(
        t,
        prime_limit=prime_limit,
        name=name or f"first-{t_size}-odd-primes",
        description=description
        or (
            "Generated by the Dinkelbach-style optimiser for a prefix T. "
            "The exact equation (11) value is recorded by the verifier."
        ),
    )


def split_targets(
    t: Sequence[int], selected: Sequence[SelectedPrime], delta: float, *, target_count: int = 150
) -> tuple[SplitTarget, ...]:
    """Return valuable selected primes that split in the current quadratic field.

    Parameters
    ----------
    t:
        Current ramified prime set.
    selected:
        Selected primes from the current optimisation.
    delta:
        Current exponent increment.
    target_count:
        Number of split primes retained for heuristic scoring.

    Returns
    -------
    tuple[SplitTarget, ...]
        Split targets sorted by descending transformed local score.
    """

    targets: list[SplitTarget] = []
    t_tuple = tuple(t)
    for item in selected:
        if not splits_in_quadratic_field_q(item.p, t_tuple):
            continue
        score, _ = best_k_score(Candidate(p=item.p, e=1, split=True), delta)
        if score > 0.0:
            targets.append(SplitTarget(p=item.p, score=score))
    targets.sort(key=lambda target: target.score, reverse=True)
    return tuple(targets[:target_count])


def swap_heuristic_score(t: Sequence[int], drop: int, add: int, targets: Sequence[SplitTarget]) -> float:
    """Score a swap by the split primes it is expected to flip to non-split.

    Parameters
    ----------
    t:
        Current ramified prime set.
    drop:
        Prime removed from ``T``.
    add:
        Prime added to ``T``.
    targets:
        Valuable selected split primes.

    Returns
    -------
    float
        Heuristic score with the discriminant penalty included.
    """

    if drop not in set(t):
        msg = "drop must belong to T"
        raise ValueError(msg)
    if add in set(t):
        msg = "add must not belong to T"
        raise ValueError(msg)

    score = 0.0
    for target in targets:
        if add == target.p:
            score += target.score
            continue
        if target.p == drop:
            continue
        if legendre_symbol(add, target.p) * legendre_symbol(drop, target.p) == -1:
            score += target.score
    return score - 0.125 * math.log(add / drop)


def propose_swaps(
    t: Sequence[int],
    selected: Sequence[SelectedPrime],
    delta: float,
    *,
    add_prime_limit: int = 1_500,
    target_split_count: int = 150,
    preserve_residue_mod_four: bool = True,
) -> list[SwapMove]:
    """Rank single-swap proposals by a splitting-pattern heuristic.

    Parameters
    ----------
    t:
        Current ramified prime set.
    selected:
        Current selected primes.
    delta:
        Current exponent increment.
    add_prime_limit:
        Upper bound for primes that may be inserted into ``T``.
    target_split_count:
        Number of valuable split primes used in the heuristic.
    preserve_residue_mod_four:
        Whether each proposal must replace a prime by one in the same residue
        class modulo ``4``.  This preserves the parity condition automatically.

    Returns
    -------
    list[SwapMove]
        Proposed moves sorted by descending heuristic score.
    """

    t_tuple = sorted_t(t)
    t_set = set(t_tuple)
    targets = split_targets(t_tuple, selected, delta, target_count=target_split_count)
    additions = [p for p in primes_up_to(add_prime_limit) if p > 2 and p not in t_set]

    # Precompute all Legendre symbols used by the heuristic.  Calling pow() in
    # the innermost drop/add/target loop makes the swap search unnecessarily
    # slow; with this cache the heuristic part is tiny compared with the exact
    # re-optimisations of promising moves.
    drop_symbols: dict[int, dict[int, int]] = {}
    add_symbols: dict[int, dict[int, int]] = {}
    for target in targets:
        drop_symbols[target.p] = {drop: legendre_symbol(drop, target.p) for drop in t_tuple}
        add_symbols[target.p] = {
            add: 0 if add == target.p else legendre_symbol(add, target.p) for add in additions
        }

    moves: list[SwapMove] = []
    for drop in t_tuple:
        for add in additions:
            if preserve_residue_mod_four and add % 4 != drop % 4:
                continue
            score = -0.125 * math.log(add / drop)
            for target in targets:
                if add == target.p:
                    score += target.score
                elif add_symbols[target.p][add] * drop_symbols[target.p][drop] == -1:
                    score += target.score
            moves.append(SwapMove(drop=drop, add=add, heuristic_score=score))
    moves.sort(key=lambda move: move.heuristic_score, reverse=True)
    return moves


def apply_swap(t: Sequence[int], move: SwapMove) -> tuple[int, ...]:
    """Apply a single swap to ``T``.

    Parameters
    ----------
    t:
        Current ramified prime set.
    move:
        Swap to apply.

    Returns
    -------
    tuple[int, ...]
        New sorted ramified prime set.
    """

    t_set = set(t)
    if move.drop not in t_set:
        msg = "drop must belong to T"
        raise ValueError(msg)
    if move.add in t_set:
        msg = "add must not belong to T"
        raise ValueError(msg)
    t_set.remove(move.drop)
    t_set.add(move.add)
    return tuple(sorted(t_set))


def swap_search(
    *,
    initial_t: Sequence[int] | None = None,
    t_size: int = 81,
    prime_limit: int = 200_000,
    add_prime_limit: int = 1_300,
    steps: int = 2,
    top_swaps: int = 2,
    target_split_count: int = 150,
    preserve_residue_mod_four: bool = True,
    name: str | None = None,
) -> SwapSearchResult:
    """Run a greedy heuristic-guided search over non-prefix choices of ``T``.

    Parameters
    ----------
    initial_t:
        Optional explicit starting set.  When omitted, the first ``t_size`` odd
        primes are used.
    t_size:
        Number of odd primes in the prefix starting set when ``initial_t`` is
        omitted.
    prime_limit:
        Candidate prime search limit for each exact optimisation.
    add_prime_limit:
        Upper bound for primes that may be swapped into ``T``.
    steps:
        Maximum number of accepted greedy steps.
    top_swaps:
        Number of heuristic proposals to optimise exactly at each step.
    target_split_count:
        Number of selected split primes used in the heuristic.
    preserve_residue_mod_four:
        Whether proposed swaps must preserve residue classes modulo ``4``.
    name:
        Optional name for the final certificate.

    Returns
    -------
    SwapSearchResult
        Initial result, best result, accepted steps, and number of exact move
        evaluations.
    """

    current_t = sorted_t(initial_t if initial_t is not None else first_odd_primes(t_size))
    initial = optimise_t(current_t, prime_limit=prime_limit, name="swap-search-initial")
    current = initial
    current_delta = exact_delta(current)
    accepted: list[SwapStep] = []
    evaluated_moves = 0

    for step_index in range(steps):
        moves = propose_swaps(
            current_t,
            current.certificate.selected,
            current_delta,
            add_prime_limit=add_prime_limit,
            target_split_count=target_split_count,
            preserve_residue_mod_four=preserve_residue_mod_four,
        )
        best_move: SwapMove | None = None
        best_result: SearchResult | None = None
        best_delta = current_delta
        for move in moves[:top_swaps]:
            candidate_t = apply_swap(current_t, move)
            result = optimise_t(
                candidate_t,
                prime_limit=prime_limit,
                name=f"swap-search-step-{step_index + 1}-{move.drop}-to-{move.add}",
            )
            evaluated_moves += 1
            candidate_delta = exact_delta(result)
            if candidate_delta > best_delta:
                best_move = move
                best_result = result
                best_delta = candidate_delta

        if best_move is None or best_result is None:
            break
        accepted.append(
            SwapStep(move=best_move, previous_delta=current_delta, new_delta=best_delta)
        )
        current = best_result
        current_t = current.certificate.t
        current_delta = best_delta

    if name is not None:
        certificate = Certificate(
            name=name,
            description=current.certificate.description,
            t=current.certificate.t,
            selected=current.certificate.selected,
            r=current.certificate.r,
        )
        current = SearchResult(
            certificate=certificate,
            approximate_delta=current.approximate_delta,
            positivity_threshold=current.positivity_threshold,
            prime_limit=current.prime_limit,
        )
    return SwapSearchResult(
        initial=initial,
        best=current,
        steps=tuple(accepted),
        evaluated_moves=evaluated_moves,
    )
