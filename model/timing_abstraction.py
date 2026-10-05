"""Concrete/abstract helpers for operation-aware timing interfaces.

Two related domains are implemented.

Deployment domain (A,Q)
-----------------------
For a compact set S of non-negative (release,duration) pairs,
  A = max(r+d), Q = max(d).
This is the fully abstract quotient for one-shot robust completion under
Cartesian-separable local uncertainty in precedence-DAG contexts.

Fusion-complete envelope domain (A,R,Q)
---------------------------------------
Adding R=max(r) yields the least three-cap envelope
  r+d <= A, r <= R, d <= Q
that contains S.  The admissible reduced-product domain satisfies
  max(R,Q) <= A <= R+Q.
This envelope family is closed under exact conjunction with a reduced meet.
The deployment projection simply drops R.

Finite timing sets are represented as Python iterables. None denotes bottom.
"""
from __future__ import annotations


def alpha(points):
    """Two-coordinate deployment abstraction (A,Q)."""
    pts = list(points)
    if not pts:
        return None
    if any(float(r) < 0 or float(d) < 0 for r, d in pts):
        raise ValueError("release and duration must be non-negative")
    A = max(float(r) + float(d) for r, d in pts)
    Q = max(float(d) for _, d in pts)
    return (A, Q)


def gamma_contains(signature, point, tol=1e-12):
    if signature is None:
        return False
    A, Q = map(float, signature)
    r, d = map(float, point)
    if A < 0 or Q < 0 or Q > A + tol or r < 0 or d < 0:
        return False
    return r + d <= A + tol and d <= Q + tol


def refines(a, b, tol=1e-12):
    """Deployment/contextual order: a is at least as tight as b."""
    if a is None:
        return True
    if b is None:
        return a is None
    return a[0] <= b[0] + tol and a[1] <= b[1] + tol


def join(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return (max(a[0], b[0]), max(a[1], b[1]))


def meet(a, b):
    """Tightest universally sound post-hoc conjunction from (A,Q) alone."""
    if a is None or b is None:
        return None
    return (min(a[0], b[0]), min(a[1], b[1]))


def envelope_alpha(points):
    """Three-coordinate envelope abstraction (A,R,Q)."""
    pts = list(points)
    if not pts:
        return None
    if any(float(r) < 0 or float(d) < 0 for r, d in pts):
        raise ValueError("release and duration must be non-negative")
    A = max(float(r) + float(d) for r, d in pts)
    R = max(float(r) for r, _ in pts)
    Q = max(float(d) for _, d in pts)
    return (A, R, Q)


def canonical_envelope_from_caps(A, R, Q):
    """Reduce possibly redundant non-negative raw upper caps to canonical (A,R,Q).

    Raw evidence denotes {r,d >= 0: r+d <= A, r <= R, d <= Q}.  The
    returned triple is the exact canonical envelope for that region.
    """
    A, R, Q = map(float, (A, R, Q))
    if A < 0 or R < 0 or Q < 0:
        raise ValueError("raw envelope caps must be non-negative")
    R_eff = min(R, A)
    Q_eff = min(Q, A)
    A_eff = min(A, R_eff + Q_eff)
    z = (A_eff, R_eff, Q_eff)
    if not envelope_valid(z):
        raise AssertionError(f"cap reduction produced invalid envelope: {z}")
    return z


def envelope_valid(z, tol=1e-12):
    if z is None:
        return True
    A, R, Q = map(float, z)
    return (
        A >= -tol and R >= -tol and Q >= -tol
        and max(R, Q) <= A + tol
        and A <= R + Q + tol
    )


def envelope_contains(z, point, tol=1e-12):
    if z is None or not envelope_valid(z, tol=tol):
        return False
    A, R, Q = map(float, z)
    r, d = map(float, point)
    if r < 0 or d < 0:
        return False
    return r + d <= A + tol and r <= R + tol and d <= Q + tol


def envelope_refines(a, b, tol=1e-12):
    """Set-inclusion order on canonical three-cap envelopes."""
    if a is None:
        return True
    if b is None:
        return a is None
    if not envelope_valid(a, tol) or not envelope_valid(b, tol):
        raise ValueError("invalid envelope signature")
    return all(float(x) <= float(y) + tol for x, y in zip(a, b))


def envelope_meet(a, b):
    """Exact conjunction in the canonical three-cap envelope family.

    Coordinatewise minima must be reduced because A cannot exceed R+Q.
    """
    if a is None or b is None:
        return None
    if not envelope_valid(a) or not envelope_valid(b):
        raise ValueError("invalid envelope signature")
    A0 = min(float(a[0]), float(b[0]))
    R = min(float(a[1]), float(b[1]))
    Q = min(float(a[2]), float(b[2]))
    A = min(A0, R + Q)
    z = (A, R, Q)
    if not envelope_valid(z):
        raise AssertionError(f"reduced meet produced invalid envelope: {z}")
    return z


def envelope_meet_many(signatures):
    """Exact n-way conjunction in the canonical envelope family."""
    zs = list(signatures)
    if not zs:
        raise ValueError("at least one signature is required")
    if any(z is None for z in zs):
        return None
    if any(not envelope_valid(z) for z in zs):
        raise ValueError("invalid envelope signature")
    A0 = min(float(z[0]) for z in zs)
    R = min(float(z[1]) for z in zs)
    Q = min(float(z[2]) for z in zs)
    return (min(A0, R + Q), R, Q)


def deployment_projection(z):
    """Forget the release cap R and expose the deployment contextual quotient."""
    if z is None:
        return None
    if not envelope_valid(z):
        raise ValueError("invalid envelope signature")
    return (float(z[0]), float(z[2]))


def projection_debt(a, b):
    """Exact source-context loss from compress-then-fuse vs envelope-fuse-then-project.

    Inputs are canonical envelope signatures. The return value is the excess A
    retained by the best (A,Q)-only post-hoc conjunction.
    """
    if a is None or b is None:
        return 0.0
    if not envelope_valid(a) or not envelope_valid(b):
        raise ValueError("invalid envelope signature")
    A0 = min(float(a[0]), float(b[0]))
    R = min(float(a[1]), float(b[1]))
    Q = min(float(a[2]), float(b[2]))
    return max(0.0, A0 - (R + Q))


def projection_debt_many(signatures):
    """Exact source-context loss for finite envelope conjunction after early projection.

    This implements the finite-family formula from Corollary 1.
    """
    zs = list(signatures)
    if not zs:
        raise ValueError("at least one signature is required")
    if any(z is None for z in zs):
        return 0.0
    if any(not envelope_valid(z) for z in zs):
        raise ValueError("invalid envelope signature")
    A0 = min(float(z[0]) for z in zs)
    R = min(float(z[1]) for z in zs)
    Q = min(float(z[2]) for z in zs)
    return max(0.0, A0 - (R + Q))


def compression_commutes(signatures, tol=1e-12):
    """Return whether project-then-conjoin equals conjoin-then-project.

    For a finite family of canonical three-cap envelopes, this is equivalent to
    zero projection debt and is decidable from the stored triples alone.
    """
    return projection_debt_many(signatures) <= tol
