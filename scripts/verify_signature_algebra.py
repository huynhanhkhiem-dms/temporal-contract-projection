#!/usr/bin/env python3
"""Finite falsification of the fully-abstract signature algebra.

This script is not a proof. It exhaustively enumerates all non-empty subsets of
{0,1,2}^2, then checks the union homomorphism and contextual transfer order on
all ordered pairs. It also searches for two pairings with identical input
signatures but different non-empty intersection signatures, witnessing that no
post-hoc conjunction operator on signatures can be exact in general.
"""
from __future__ import annotations
import itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from model.structure_oracle import timing_signature_from_points

GRID=[(r,d) for r in range(3) for d in range(3)]
SETS=[]
for mask in range(1,1<<len(GRID)):
    S=frozenset(GRID[i] for i in range(len(GRID)) if mask>>i & 1)
    SETS.append(S)
SIG={S:timing_signature_from_points(S) for S in SETS}


def transfer(sig,x):
    A,Q=sig
    return max(A,x+Q)

pairs=0; union_mismatch=0; preorder_mismatch=0; intersection_pairs=0
# Integer-grid signatures have breakpoints among integer A values; half-step probes
# around all possible breakpoints are sufficient as a finite falsification suite.
X=[i/2 for i in range(0,13)]
for S in SETS:
    As,Qs=SIG[S]
    for T in SETS:
        pairs += 1
        At,Qt=SIG[T]
        U=S|T
        expected=(max(As,At),max(Qs,Qt))
        if SIG[U] != expected:
            union_mismatch += 1
        comp_order=(As<=At and Qs<=Qt)
        transfer_order=all(transfer(SIG[S],x)<=transfer(SIG[T],x)+1e-12 for x in X)
        if comp_order != transfer_order:
            preorder_mismatch += 1
        if S & T:
            intersection_pairs += 1
            Ai,Qi=SIG[S&T]
            if Ai>min(As,At)+1e-12 or Qi>min(Qs,Qt)+1e-12:
                raise AssertionError('intersection monotonicity violated')

# Constructive non-identifiability witness from the theorem.
P=frozenset({(0,2),(3,0)})
R=frozenset({(1,2),(3,0)})
# The witness uses coordinate 3, outside GRID, intentionally: it is a theorem
# witness rather than part of the small-grid enumeration.
sigP=timing_signature_from_points(P); sigR=timing_signature_from_points(R)
witness={
    'input_signature_P':sigP,
    'input_signature_R':sigR,
    'intersection_PP':timing_signature_from_points(P & P),
    'intersection_PR':timing_signature_from_points(P & R),
}
assert sigP==sigR==(3.0,2.0)
assert witness['intersection_PP']==(3.0,2.0)
assert witness['intersection_PR']==(3.0,0.0)

out={
    'grid_points':len(GRID),
    'nonempty_sets':len(SETS),
    'ordered_set_pairs':pairs,
    'nonempty_intersection_pairs':intersection_pairs,
    'union_mismatches':union_mismatch,
    'contextual_preorder_probe_mismatches':preorder_mismatch,
    'probe_x_values':X,
    'posthoc_conjunction_nonidentifiability_witness':witness,
}
if union_mismatch or preorder_mismatch:
    raise SystemExit(out)
path=ROOT/'outputs'/'signature_algebra_exhaustive.json'
path.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
