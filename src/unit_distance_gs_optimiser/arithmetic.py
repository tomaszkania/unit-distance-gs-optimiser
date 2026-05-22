"""Elementary arithmetic used by the Sawin parameter verifier."""

from __future__ import annotations

import math
from collections.abc import Iterable


def primes_up_to(limit: int) -> list[int]:
    """Return all primes not exceeding ``limit``.

    Parameters
    ----------
    limit:
        Upper bound for the sieve.

    Returns
    -------
    list[int]
        Primes ``p`` with ``p <= limit``.
    """

    if limit < 2:
        return []
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for n in range(2, math.isqrt(limit) + 1):
        if sieve[n]:
            start = n * n
            sieve[start : limit + 1 : n] = b"\x00" * (((limit - start) // n) + 1)
    return [n for n in range(limit + 1) if sieve[n]]


def is_prime(n: int) -> bool:
    """Check primality by trial division.

    Parameters
    ----------
    n:
        Integer to test.

    Returns
    -------
    bool
        ``True`` exactly when ``n`` is prime.
    """

    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    for divisor in range(3, math.isqrt(n) + 1, 2):
        if n % divisor == 0:
            return False
    return True


def first_odd_primes(count: int) -> list[int]:
    """Return the first ``count`` odd primes.

    Parameters
    ----------
    count:
        Number of odd primes requested.

    Returns
    -------
    list[int]
        Prefix of the odd primes.
    """

    if count < 0:
        msg = "count must be non-negative"
        raise ValueError(msg)
    limit = 16
    while True:
        odd_primes = [p for p in primes_up_to(limit) if p > 2]
        if len(odd_primes) >= count:
            return odd_primes[:count]
        limit *= 2


def legendre_symbol(a: int, p: int) -> int:
    """Compute the Legendre symbol ``(a / p)``.

    Parameters
    ----------
    a:
        Integer numerator.
    p:
        Odd prime modulus.

    Returns
    -------
    int
        One of ``-1``, ``0`` or ``1``.
    """

    if p == 2 or not is_prime(p):
        msg = "p must be an odd prime"
        raise ValueError(msg)
    residue = a % p
    if residue == 0:
        return 0
    value = pow(residue, (p - 1) // 2, p)
    return -1 if value == p - 1 else value


def product_mod(values: Iterable[int], modulus: int) -> int:
    """Compute a product modulo ``modulus``.

    Parameters
    ----------
    values:
        Factors in the product.
    modulus:
        Positive modulus.

    Returns
    -------
    int
        Product of the factors modulo ``modulus``.
    """

    if modulus <= 0:
        msg = "modulus must be positive"
        raise ValueError(msg)
    result = 1 % modulus
    for value in values:
        result = (result * (value % modulus)) % modulus
    return result


def quadratic_character_of_product(values: Iterable[int], p: int) -> int:
    """Compute ``(prod(values) / p)`` as a Legendre symbol.

    Parameters
    ----------
    values:
        Integer factors.
    p:
        Odd prime modulus.

    Returns
    -------
    int
        Legendre symbol of the product.
    """

    return legendre_symbol(product_mod(values, p), p)
