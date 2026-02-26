from random import randrange
import functools
import math

import sympy as sym
from sympy import GF

from Polynomial import Zx


def cyclic_convolution(F, G, n):
    result = F.multiply(G)
    t = Zx([0] * n)
    for i in range(result.degree() + 1):
        t.coeffs[i % n] += result.coeffs[i]
    return t


def balancedmodulus(F, q, n):
    result = Zx([])
    for i in range(n):
        coeff = F.coefficient(i) if hasattr(F, 'coefficient') else F.coeffs[i]
        result.coeffs.append(((coeff + q // 2) % q) - q // 2)
    return result


def normalize(poly):
    while poly and poly[-1] == 0:
        poly.pop()
    if not poly:
        poly.append(0)


def poly_divmod(X, Y):
    num = X.coeffs[:]
    den = Y.coeffs[:]
    normalize(num)
    normalize(den)

    if len(num) < len(den):
        quotient = Zx([0])
        remainder = Zx(num)
        return quotient, remainder

    shift_len = len(num) - len(den)
    den = [0] * shift_len + den

    quot = []
    divisor = float(den[-1])
    for _ in range(shift_len + 1):
        mult = num[-1] / divisor
        quot = [mult] + quot
        if mult != 0:
            d = [mult * u for u in den]
            num = [u - v for u, v in zip(num, d)]
        num.pop()
        den.pop(0)

    normalize(num)
    quotient = Zx(quot)
    remainder = Zx(num)
    return quotient, remainder


def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def make_poly(coeffs):
    x = sym.Symbol('x')
    coeffs = list(reversed(coeffs))
    y = 0
    for i, coeff in enumerate(coeffs):
        y += (x ** i) * coeff
    return sym.poly(y)


def invertmodprime(F, N, p):
    f_poly = make_poly(F.coeffs[::-1])
    x = sym.Symbol('x')
    t = sym.polys.polytools.invert(f_poly, x ** N - 1, domain=GF(p, symmetric=False))
    fp = Zx([])
    fp.coeffs = t.all_coeffs()[::-1]
    return fp


def log2(x):
    if x <= 0:
        return False
    return math.log10(x) / math.log10(2)


def is_power_of_two(n):
    return isinstance(n, int) and n > 0 and (n & (n - 1)) == 0


def invertmodpowerof2(F, N, q, max_iterations=128):
    if not is_power_of_two(q):
        raise ValueError('q has to be a power of 2')

    g = invertmodprime(F, N, 2)
    two = Zx([2])

    for _ in range(max_iterations):
        r = balancedmodulus(cyclic_convolution(F, g, N), q, N)
        if r.coeffs[0] == 1 and all(coeff == 0 for coeff in r.coeffs[1:]):
            return g

        l = two.add(r.multiply_single_term(-1, 0))
        g = balancedmodulus(cyclic_convolution(g, l, N), q, N)

    raise RuntimeError('invertmodpowerof2 did not converge')


def generate_keypair(p, q, d, N, max_attempts=2000):
    last_error = None
    for _ in range(max_attempts):
        try:
            F = Zx([])
            F.randompoly(d, N)
            F_inverse = invertmodprime(F, N, p)
            Fq = invertmodpowerof2(F, N, q)

            g = Zx([])
            g.randompoly(d, N)

            t = cyclic_convolution(Fq, g, N).multiply(Zx([p]))
            public_key = balancedmodulus(t, q, N)
            secret_key = (F, F_inverse)
            return public_key, secret_key
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(f'Failed to generate keypair after {max_attempts} attempts: {last_error}')


def encrypt(message, public_key, d, N, q):
    r = Zx([])
    r.randompoly(d, N)
    return balancedmodulus(cyclic_convolution(public_key, r, N).add(message), q, N)


def decrypt(cipher_text, private_key, p, q, N):
    F, F_inverse = private_key
    a = balancedmodulus(cyclic_convolution(cipher_text, F, N), q, N)
    return balancedmodulus(cyclic_convolution(a, F_inverse, N), p, N)


def cross_check(decrypted_message, plain_text):
    ok = functools.reduce(
        lambda i, j: i and j,
        map(lambda m, k: m == k, plain_text.coeffs, decrypted_message.coeffs),
        True,
    )
    if ok:
        print('Successful!')
    else:
        print('Error!!!')


# Backward-compatible aliases
Log2 = log2
isPowerOfTwo = is_power_of_two
