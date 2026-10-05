#!/usr/bin/env python3
"""Exhaustive finite check of the operator-relative full-abstraction theorem.

For every ordered pair of admissible integer envelopes z1,z2 with coordinates
bounded by MAX, compute the semantic preorder directly obtained by:
  1) conjoining each candidate with every admissible envelope probe h, then
  2) evaluating the resulting deployment transfer for predecessor arrivals x.

The semantic preorder must agree exactly with coordinatewise order on (A,R,Q).
The checker deliberately reimplements meet/projection/transfer locally instead of
calling model.timing_abstraction.
"""
from __future__ import annotations
from itertools import product
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
MAX=6
XMAX=12


def valid(z):
    A,R,Q=z
    return 0 <= R <= A and 0 <= Q <= A and A <= R+Q


def meet3(a,h):
    A=min(a[0],h[0],min(a[1],h[1])+min(a[2],h[2]))
    return (A,min(a[1],h[1]),min(a[2],h[2]))


def transfer_after_probe(z,h,x):
    A,_,Q=meet3(z,h)
    return max(A,x+Q)


def coordinate_refines(a,b):
    return a[0] <= b[0] and a[1] <= b[1] and a[2] <= b[2]

D=[z for z in product(range(MAX+1),repeat=3) if valid(z)]
xs=list(range(XMAX+1))
pair_checks=0
semantic_evaluations=0
mismatches=[]
for a in D:
    for b in D:
        pair_checks += 1
        predicted=coordinate_refines(a,b)
        semantic=True
        witness=None
        for h in D:
            for x in xs:
                semantic_evaluations += 1
                left=transfer_after_probe(a,h,x)
                right=transfer_after_probe(b,h,x)
                if left > right:
                    semantic=False
                    witness={'probe':h,'x':x,'left':left,'right':right}
                    break
            if not semantic:
                break
        if semantic != predicted:
            mismatches.append({'a':a,'b':b,'coordinatewise':predicted,'semantic':semantic,'witness':witness})
            if len(mismatches)>=10:
                break
    if len(mismatches)>=10:
        break

# Point-set cross-check of the two symbolic operations on a smaller domain.
PS_MAX=4
PS_XMAX=8


def env_points(z):
    A,R,Q=z
    return frozenset((r,d) for r in range(PS_MAX+1) for d in range(PS_MAX+1)
                     if r+d<=A and r<=R and d<=Q)


def beta(S):
    return (max(r+d for r,d in S), max(r for r,d in S), max(d for r,d in S))


D_ps=[z for z in product(range(PS_MAX+1),repeat=3) if valid(z)]
ps_pairs=0; ps_transfer_evals=0
ps_meet_mismatches=0; ps_transfer_mismatches=0
for a in D_ps:
    Sa=env_points(a)
    for h in D_ps:
        ps_pairs += 1
        Sm=Sa & env_points(h)
        if beta(Sm) != meet3(a,h):
            ps_meet_mismatches += 1
        for x in range(PS_XMAX+1):
            ps_transfer_evals += 1
            if max(max(r,x)+d for r,d in Sm) != transfer_after_probe(a,h,x):
                ps_transfer_mismatches += 1

# Separately check the two proof probes on every pair: a large identity probe
# exposes A/Q, while a zero-duration probe exposes R.
top=(MAX,MAX,MAX)
rprobe=(MAX,MAX,0)
proof_probe_mismatches=0
for a in D:
    if meet3(a,top) != a:
        proof_probe_mismatches += 1
    Ar,_,Qr=meet3(a,rprobe)
    if (Ar,Qr)!=(a[1],0):
        proof_probe_mismatches += 1

out={
    'integer_bound':MAX,
    'predecessor_x_max':XMAX,
    'admissible_envelopes':len(D),
    'ordered_envelope_pairs':pair_checks,
    'semantic_probe_evaluations':semantic_evaluations,
    'contextual_preorder_mismatches':len(mismatches),
    'proof_probe_mismatches':proof_probe_mismatches,
    'point_set_bound':PS_MAX,
    'point_set_envelopes':len(D_ps),
    'point_set_pairs':ps_pairs,
    'point_set_transfer_evaluations':ps_transfer_evals,
    'point_set_meet_mismatches':ps_meet_mismatches,
    'point_set_transfer_mismatches':ps_transfer_mismatches,
    'first_mismatches':mismatches,
}
if mismatches or proof_probe_mismatches or ps_meet_mismatches or ps_transfer_mismatches:
    raise SystemExit(out)
path=ROOT/'outputs'/'operation_relative_contexts_exhaustive.json'
path.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
