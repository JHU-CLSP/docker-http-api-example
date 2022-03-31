#!/usr/bin/env python3

from itertools import count, takewhile
from math import prod
from typing import Generator, List, Tuple

Factorization = List[Tuple[int, int]]


def compute_product(factorization: Factorization) -> int:
    return prod(pow(b, e) for (b, e) in factorization)


def is_prime(n: int) -> bool:
    def _square_is_le_n(m: int) -> bool:
        return m * m <= n

    return all(n % m != 0 for m in takewhile(_square_is_le_n, count(start=2)))


def generate_primes(start: int = 2) -> Generator[int, None, None]:
    return (n for n in count(start=start) if is_prime(n))


def is_factor(m: int, n: int) -> bool:
    return n % m == 0


def compute_factor_exponent(b: int, n: int) -> int:
    def _power_is_factor(e: int) -> bool:
        return is_factor(pow(b, e), n)

    return list(takewhile(_power_is_factor, count(start=0)))[-1]


def factorize(n: int) -> Factorization:
    if n < 2:
        raise Exception('Can only factorize integers greater than 1.')

    else:
        factorization: Factorization = []
        while compute_product(factorization) != n:
            primes = generate_primes(factorization[-1][0] + 1 if factorization else 2)
            b = next(p for p in primes if is_factor(p, n))
            factorization.append((b, compute_factor_exponent(b, n)))

        return factorization
