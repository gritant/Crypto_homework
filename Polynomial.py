from random import randrange


class Zx:
    def __init__(self, coeffs):
        self.coeffs = coeffs

    def coefficient(self, n):
        if not isinstance(n, int) or n < 0:
            raise ValueError('Coefficient index does not exist')
        if n >= len(self.coeffs):
            return 0
        return self.coeffs[n]

    def degree(self):
        return len(self.coeffs) - 1

    def eval(self, x):
        result = 0
        for i, coeff in enumerate(self.coeffs):
            result += coeff * (x ** i)
        return result

    def add(self, other):
        length = max(self.degree(), other.degree()) + 1
        result = [0] * length
        for i in range(length):
            result[i] = self.coefficient(i) + other.coefficient(i)
        return Zx(result)

    def multiply_single_term(self, coefficient, degree):
        result = Zx(self.coeffs[:])
        result.coeffs[0:0] = [0] * degree
        for i in range(len(result.coeffs)):
            result.coeffs[i] *= coefficient
        return result

    def multiply(self, other):
        if self.degree() < 0 or other.degree() < 0:
            return Zx([0])

        result = [0] * (len(self.coeffs) + len(other.coeffs) - 1)
        for i, a in enumerate(self.coeffs):
            if a == 0:
                continue
            for j, b in enumerate(other.coeffs):
                if b == 0:
                    continue
                result[i + j] += a * b
        return Zx(result)

    def print_polynomial(self):
        terms = []
        for i, coeff in enumerate(self.coeffs):
            if i == 0:
                terms.append(str(coeff))
            elif i == 1:
                terms.append(f'{coeff}x')
            else:
                terms.append(f'{coeff}x^{i}')
        terms.reverse()
        return '+'.join(terms)

    def randompoly(self, d, n):
        self.coeffs = [0] * n
        for _ in range(d):
            while True:
                r = randrange(n)
                if self.coeffs[r] == 0:
                    break
            self.coeffs[r] = 1 - 2 * randrange(2)
        self.print_polynomial()
