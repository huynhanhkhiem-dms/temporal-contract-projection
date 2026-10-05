#!/usr/bin/env python3
"""Finite falsification for the abstract-domain results.

Checks a 3x3 release/duration grid exhaustively.  The analytical proofs in the
paper remain primary; this script is a finite regression layer for:
- the Galois insertion / canonical closure,
- exact abstract join for union,
- soundness and optimality of coordinatewise meet as signature-only fusion,
- a recovered non-identifiability witness for exact conjunction,
- an explicit family showing unbounded conservatism of signature-only fusion.
"""
from __future__ import annotations
from itertools import combinations
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
GRID=[(r,d) for r in range(3) for d in range(3)]


def alpha(S):
    if not S:
        return None
    return (max(r+d for r,d in S), max(d for r,d in S))


def leq(a,b):
    if a is None:
        return True
    if b is None:
        return a is None
    return a[0] <= b[0] and a[1] <= b[1]


def join(a,b):
    if a is None: return b
    if b is None: return a
    return (max(a[0],b[0]), max(a[1],b[1]))


def meet(a,b):
    if a is None or b is None: return None
    return (min(a[0],b[0]), min(a[1],b[1]))


def gamma_grid(z):
    if z is None:
        return frozenset()
    A,Q=z
    return frozenset((r,d) for r,d in GRID if r+d <= A and d <= Q)

sets=[]
for mask in range(1,1<<len(GRID)):
    sets.append(frozenset(GRID[i] for i in range(len(GRID)) if mask>>i & 1))

closure_extensive=closure_idempotent=gi_mismatches=union_mismatches=meet_sound_mismatches=0
sig_groups={}
for S in sets:
    a=alpha(S)
    sig_groups.setdefault(a,[]).append(S)
    C=gamma_grid(a)
    if not S.issubset(C): closure_extensive += 1
    if gamma_grid(alpha(C)) != C: closure_idempotent += 1

# alpha(S) <= z iff S subset gamma(z), for every realized z
realized=sorted(sig_groups)
for S in sets:
    a=alpha(S)
    for z in realized:
        if (leq(a,z)) != S.issubset(gamma_grid(z)):
            gi_mismatches += 1

for S in sets:
    a=alpha(S)
    for T in sets:
        b=alpha(T)
        if alpha(S|T) != join(a,b):
            union_mismatches += 1
        I=S&T
        if I:
            ai=alpha(I); m=meet(a,b)
            if not leq(ai,m): meet_sound_mismatches += 1

# Tightness of the signature-only meet: canonical representatives attain it.
meet_optimality_mismatches=0
for a in realized:
    for b in realized:
        m=meet(a,b)
        C=gamma_grid(a)&gamma_grid(b)
        if C and alpha(C) != m:
            meet_optimality_mismatches += 1

# Recover two pairs with identical input signatures but different intersection signatures.
witness=None
for a,group in sig_groups.items():
    if len(group)<2: continue
    for S in group:
        for T in group:
            I=S&T
            if not I: continue
            ai=alpha(I)
            if ai != a:
                witness={
                    'input_signature':a,
                    'left':sorted(S),
                    'right':sorted(T),
                    'intersection':sorted(I),
                    'intersection_signature':ai,
                }
                break
        if witness: break
    if witness: break

# Analytical family illustrating arbitrarily conservative optimal post-hoc fusion.
family=[]
for M in [2,4,8,16,32,64,128]:
    S={(0,M),(0,1)}
    T={(M,0),(0,1)}
    a=alpha(S); b=alpha(T); m=meet(a,b); exact=alpha(S&T)
    family.append({
        'M':M,'alpha_S':a,'alpha_T':b,'signature_only_meet':m,
        'exact_intersection_signature':exact,
        'isolated_completion_ratio':m[0]/exact[0],
    })

out={
    'grid_points':len(GRID),
    'nonempty_sets':len(sets),
    'realized_signatures':len(realized),
    'galois_insertion_mismatches':gi_mismatches,
    'closure_extensivity_mismatches':closure_extensive,
    'closure_idempotence_mismatches':closure_idempotent,
    'union_mismatches':union_mismatches,
    'meet_soundness_mismatches':meet_sound_mismatches,
    'canonical_meet_optimality_mismatches':meet_optimality_mismatches,
    'nonidentifiability_witness':witness,
    'unbounded_conservatism_family':family,
}
if any(out[k] for k in [
    'galois_insertion_mismatches','closure_extensivity_mismatches',
    'closure_idempotence_mismatches','union_mismatches',
    'meet_soundness_mismatches','canonical_meet_optimality_mismatches']):
    raise SystemExit(out)
if witness is None: raise SystemExit('no conjunction witness recovered')
path=ROOT/'outputs'/'abstract_domain_exhaustive.json'
path.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
