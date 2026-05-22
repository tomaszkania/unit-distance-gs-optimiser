"""Tests for elementary arithmetic helpers."""

from __future__ import annotations

from unit_distance_gs_optimiser.arithmetic import first_odd_primes, legendre_symbol, primes_up_to
from unit_distance_gs_optimiser.model import (
    count_three_mod_four,
    golod_shafarevich_capacity,
    is_admissible_for_s_q,
    splits_in_quadratic_field_q,
)


def test_primes_up_to() -> None:
    """The sieve returns the expected small primes."""

    assert primes_up_to(20) == [2, 3, 5, 7, 11, 13, 17, 19]


def test_first_odd_primes() -> None:
    """The helper omits 2 and returns a prefix."""

    assert first_odd_primes(5) == [3, 5, 7, 11, 13]


def test_legendre_symbol() -> None:
    """Legendre symbols agree with small hand checks."""

    assert legendre_symbol(5, 3) == -1
    assert legendre_symbol(4, 7) == 1
    assert legendre_symbol(7, 7) == 0


def test_t81_capacity_and_parity() -> None:
    """The selected T-prefix has the advertised parity and capacity."""

    t = first_odd_primes(81)
    assert t[-1] == 421
    assert count_three_mod_four(t) == 41
    assert golod_shafarevich_capacity(t) == 1518


def test_local_conditions_for_small_primes() -> None:
    """Small primes in Sawin's original examples satisfy the local condition."""

    t = first_odd_primes(13)
    assert is_admissible_for_s_q(2, t)
    assert is_admissible_for_s_q(47, t)
    assert not splits_in_quadratic_field_q(3, t)
