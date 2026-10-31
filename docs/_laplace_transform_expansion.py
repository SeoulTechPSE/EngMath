# Process Systems Lab., SeoulTech
# April 15, 2021 Authored by Kee-Youn Yoo
# April 4, 2024 Modified for sympy version 1.12
# November 2026 Rewritten for sympy 1.14: sympy.laplace_transform now handles
#   derivatives, both translation theorems, scaling f(a t) and t**n f(t) itself,
#   and sympy.laplace_correspondence / sympy.laplace_initial_conds replace the
#   old subs_() helper. This wrapper only adds the rules sympy still lacks:
#     * integrals from 0 to t           L{int_0^t h dtau}               = L{h}/s
#     * convolution integrals            L{int_0^t f(tau) g(t-tau) dtau} = F G
#     * powers of t                      L{t**k h}  = (-1)**k d^k/ds^k L{h}
#     * exponential factors              L{exp(c t) h} = L{h}(s - c)
#   (sympy 1.14 raises "Can't calculate derivative wrt s + c" for exp(c t) t f(t)
#   and returns a garbled sum for t**m t**n f(t).)

import sympy


def _is_zero_to_t(limits, t):
    _, lo, hi = limits
    return lo == 0 and hi == t


def _convolution_factors(h, tau, t):
    """Split h into A(tau) * B(t - tau) if possible; return (A, B) or None."""
    u = sympy.Dummy('u')
    A, B = sympy.Integer(1), sympy.Integer(1)
    for fac in sympy.Mul.make_args(h):
        if t not in fac.free_symbols:
            A *= fac                       # depends on tau only
        elif tau not in fac.subs(t, tau + u).free_symbols:
            B *= fac                       # depends on t - tau only
        else:
            return None
    if A.has(tau) and B.has(t):
        return A, B
    return None


def laplace_transform_(expr, t, s):
    """Laplace transform of expr(t): sympy.laplace_transform plus the rules above."""
    expr = sympy.sympify(expr)

    if expr.is_Add:
        return sympy.Add(*[laplace_transform_(term, t, s) for term in expr.args])

    if isinstance(expr, sympy.Integral) and _is_zero_to_t(expr.limits[-1], t):
        tau = expr.limits[-1][0]
        if len(expr.limits) == 1:
            ab = _convolution_factors(expr.function, tau, t)
            if ab is not None:                                   # convolution theorem
                A, B = ab
                return (laplace_transform_(A.subs(tau, t), t, s)
                        * laplace_transform_(B.subs(t, t + tau), t, s))
            inner = expr.function
        else:                                                    # repeated integral
            inner = sympy.Integral(expr.function, *expr.limits[:-1])
        return laplace_transform_(inner.subs(tau, t), t, s) / s

    if expr.is_Mul:
        const, rest = expr.as_independent(t)
        if const != 1:
            return const * laplace_transform_(rest, t, s)
        rest = sympy.powsimp(rest)                               # t**m * t**n -> t**(m + n)
        # exp(c t) first: differentiating LaplaceTransform(f, t, s + c) with respect to s
        # is evaluated incorrectly (as 0) by sympy, so the shift must be applied last
        for fac in sympy.Mul.make_args(rest):
            if isinstance(fac, sympy.exp):                       # first translation theorem
                c = sympy.cancel(fac.args[0] / t)
                if not c.has(t):                                 # transform in a dummy variable,
                    sigma = sympy.Dummy('sigma')                 # then shift: s -> s - c
                    return laplace_transform_(rest / fac, t, sigma).subs(sigma, s - c)
        for fac in sympy.Mul.make_args(rest):
            base, k = fac.as_base_exp()
            if base == t and not k.has(t) and (k.is_integer or k.is_Symbol):
                h = rest / fac                                   # derivative of the transform
                return (-1)**k * sympy.diff(laplace_transform_(h, t, s), (s, k))

    return sympy.laplace_transform(expr, t, s, noconds=True)
