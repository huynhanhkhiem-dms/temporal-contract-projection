#!/usr/bin/env python3
"""Finite falsification check for the two-scalar timing-signature theorem.

Randomly generates DAGs and arbitrary finite (possibly nonconvex) local timing
sets. The candidate robust upper bound is computed from only A=max(r+d) and
Q=max(d); the check directly enumerates Cartesian-product realizations
and evaluates the original completion recurrence.
"""
from __future__ import annotations
import itertools, json, random
from pathlib import Path

SEED=2026091407
CASES=10000
MAX_N=5
MAX_PRODUCT=5000
OUT=Path(__file__).resolve().parents[1]/'outputs'/'general_signature_random_falsification.json'


def topo(n, edges):
    pred=[[] for _ in range(n)]
    for u,v in edges: pred[v].append(u)
    return pred


def completion(n, pred, realization):
    C=[0.0]*n
    for v in range(n):
        r,d=realization[v]
        x=max((C[u] for u in pred[v]), default=0.0)
        C[v]=max(r,x)+d
    return max(C, default=0.0)


def signature_bound(n, pred, local_sets):
    W=[0.0]*n
    for v,S in enumerate(local_sets):
        A=max(r+d for r,d in S)
        Q=max(d for _,d in S)
        x=max((W[u] for u in pred[v]), default=0.0)
        W[v]=max(A,x+Q)
    return max(W, default=0.0)


def random_set(rng):
    m=rng.randint(1,4)
    pts=set()
    while len(pts)<m:
        # quarter-step grid avoids floating comparison noise while permitting
        # arbitrary/nonconvex local sets.
        pts.add((rng.randint(0,24)/4.0, rng.randint(0,24)/4.0))
    return sorted(pts)


def main():
    rng=random.Random(SEED)
    mismatches=[]
    realizations=0
    accepted=0
    generated=0
    max_product=0
    while accepted<CASES:
        generated+=1
        n=rng.randint(1,MAX_N)
        p=rng.uniform(0.12,0.55)
        edges=[(i,j) for i in range(n) for j in range(i+1,n) if rng.random()<p]
        pred=topo(n,edges)
        sets=[random_set(rng) for _ in range(n)]
        prod=1
        for S in sets: prod*=len(S)
        if prod>MAX_PRODUCT:
            continue
        candidate=signature_bound(n,pred,sets)
        brute=-1.0
        for realization in itertools.product(*sets):
            brute=max(brute,completion(n,pred,realization))
        realizations+=prod
        max_product=max(max_product,prod)
        accepted+=1
        if abs(candidate-brute)>1e-10:
            mismatches.append({
                'case':accepted,'n':n,'edges':edges,'sets':sets,
                'signature_bound':candidate,'brute':brute,
            })
            if len(mismatches)>=10:
                break
    payload={
        'seed':SEED,
        'requested_cases':CASES,
        'accepted_cases':accepted,
        'generated_candidates':generated,
        'max_nodes':MAX_N,
        'max_cartesian_product':max_product,
        'realization_evaluations':realizations,
        'mismatches':len(mismatches),
        'first_mismatches':mismatches,
        'scope':'arbitrary finite non-negative local (release,duration) sets; direct DAG recurrence enumeration',
    }
    OUT.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload,indent=2))
    raise SystemExit(1 if mismatches else 0)

if __name__=='__main__':
    main()
