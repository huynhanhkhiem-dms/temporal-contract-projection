#!/usr/bin/env python3
"""Finite falsification/regression checks for the fusion-complete envelope theorems.

The analytical proofs in the manuscript are primary. This checker enumerates a
bounded integer realization of the continuous three-cap domain and verifies:
  * beta(E(A,R,Q))=(A,R,Q) for every admissible integer envelope;
  * exact intersection equals the reduced meet;
  * dropping R preserves one-shot transfer semantics;
  * the closed-form projection debt equals the source-context loss;
  * the zero-debt commutation criterion is exact;
  * the finite-family formula is checked directly on a smaller exhaustive
    three-source domain;
  * every pair of distinct release caps sharing (A,Q) is separated by the
    constructive future-conjunction probe used in the proof.
"""
from __future__ import annotations
from itertools import product
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
MAX=7
XMAX=10


def valid(z):
    A,R,Q=z
    return 0<=R<=A and 0<=Q<=A and A<=R+Q


def env(z):
    A,R,Q=z
    return frozenset((r,d) for r in range(MAX+1) for d in range(MAX+1)
                     if r+d<=A and r<=R and d<=Q)


def beta(S):
    if not S: return None
    return (max(r+d for r,d in S),max(r for r,d in S),max(d for r,d in S))


def proj(z):
    if z is None: return None
    return (z[0],z[2])


def meet3(a,b):
    A0=min(a[0],b[0]); R=min(a[1],b[1]); Q=min(a[2],b[2])
    return (min(A0,R+Q),R,Q)


def transfer(S,x):
    return max(max(r,x)+d for r,d in S)


def transfer2(aq,x):
    A,Q=aq
    return max(A,x+Q)


def projection_debt_local(a,b):
    A0=min(a[0],b[0]); R=min(a[1],b[1]); Q=min(a[2],b[2])
    return max(0,A0-(R+Q))

D=[z for z in product(range(MAX+1),repeat=3) if valid(z)]
reconstruction=intersection=transfer_mismatches=projection_debt_mismatches=commutation_mismatches=0
pair_checks=0
for z in D:
    S=env(z)
    if beta(S)!=z:
        reconstruction+=1
    for x in range(XMAX+1):
        if transfer(S,x)!=transfer2(proj(z),x):
            transfer_mismatches+=1

for a in D:
    Sa=env(a)
    for b in D:
        pair_checks+=1
        Sb=env(b)
        m=meet3(a,b)
        I=Sa&Sb
        if beta(I)!=m:
            intersection+=1
        post=(min(a[0],b[0]),min(a[2],b[2]))
        exact=proj(m)
        if post[0]-exact[0]!=projection_debt_local(a,b):
            projection_debt_mismatches+=1
        # At source context x=0, A is the completion because A>=Q.
        if transfer2(post,0)-transfer2(exact,0)!=projection_debt_local(a,b):
            projection_debt_mismatches+=1
        predicted_commutes = min(a[0],b[0]) <= min(a[1],b[1]) + min(a[2],b[2])
        actual_commutes = post == exact
        if predicted_commutes != actual_commutes:
            commutation_mismatches += 1

# Exhaustive three-source check on a smaller integer domain.
SMALL=4
D3=[z for z in product(range(SMALL+1),repeat=3) if valid(z)]
three_source_cases=three_source_mismatches=0
for a in D3:
    for b in D3:
        for c in D3:
            three_source_cases += 1
            I=env(a)&env(b)&env(c)
            R=min(a[1],b[1],c[1]); Q=min(a[2],b[2],c[2]); A0=min(a[0],b[0],c[0])
            exact3=(min(A0,R+Q),R,Q)
            post3=(A0,Q)
            debt3=max(0,A0-(R+Q))
            if beta(I)!=exact3 or post3[0]-exact3[0]!=debt3:
                three_source_mismatches += 1

# Separation theorem for all same-(A,Q) envelopes with distinct R.
separation_cases=separation_mismatches=0
for A in range(1,MAX+1):
    for Q in range(A+1):
        Rs=[R for R in range(A+1) if valid((A,R,Q))]
        for i,R1 in enumerate(Rs):
            for R2 in Rs[i+1:]:
                separation_cases+=1
                narrow=(A,R1,Q); wide=(A,R2,Q)
                probe=(A,A,A-R2)
                left=proj(meet3(narrow,probe))
                right=proj(meet3(wide,probe))
                if not (left[0] < right[0] and left[1]==right[1]):
                    separation_mismatches+=1


# Explicit envelope family from Theorem 6: z1=(M,1,M), z2=(M,M,1).
# Early projection gives A=M while exact envelope fusion gives A=2, so the
# source-context ratio is M/2 and additive debt M-2.
unbounded_family=[]
for M in [4,8,16,32,64,128]:
    z1=(M,1,M); z2=(M,M,1)
    exact=proj(meet3(z1,z2)); post=(min(z1[0],z2[0]),min(z1[2],z2[2]))
    assert exact==(2,1) and post==(M,1)
    unbounded_family.append({'M':M,'exact':exact,'post':post,'ratio':post[0]/exact[0],'projection_debt':post[0]-exact[0]})

out={
    'integer_bound':MAX,
    'admissible_envelopes':len(D),
    'ordered_envelope_pairs':pair_checks,
    'reconstruction_mismatches':reconstruction,
    'intersection_reduced_meet_mismatches':intersection,
    'deployment_transfer_mismatches':transfer_mismatches,
    'projection_debt_mismatches':projection_debt_mismatches,
    'commutation_condition_mismatches':commutation_mismatches,
    'three_source_cases':three_source_cases,
    'three_source_mismatches':three_source_mismatches,
    'release_cap_separation_cases':separation_cases,
    'release_cap_separation_mismatches':separation_mismatches,
    'theorem6_M_over_2_family':unbounded_family,
}
if any(out[k] for k in [
    'reconstruction_mismatches','intersection_reduced_meet_mismatches',
    'deployment_transfer_mismatches','projection_debt_mismatches',
    'commutation_condition_mismatches','three_source_mismatches',
    'release_cap_separation_mismatches']):
    raise SystemExit(out)
path=ROOT/'outputs'/'projection_complete_envelope_exhaustive.json'
path.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
