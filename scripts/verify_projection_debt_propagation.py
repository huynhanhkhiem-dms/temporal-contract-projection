#!/usr/bin/env python3
"""Finite falsification check for the non-amplification theorem for projection debt.

The checker does not call projection_debt_propagation().  It builds two signature
recurrences directly and verifies the per-vertex ancestor bound and global
max-local-debt bound.  It uses both exhaustive small signature scenarios and
random envelope-derived fusion scenarios.
"""
from __future__ import annotations
import itertools, json, random, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from model.timing_abstraction import envelope_meet, deployment_projection

OUT=ROOT/'outputs'/'projection_debt_propagation_falsification.json'
SEED=2026091423


def topo(nodes, edges):
    pred={v:[] for v in nodes}; succ={v:[] for v in nodes}; indeg={v:0 for v in nodes}
    for u,v in edges:
        pred[v].append(u); succ[u].append(v); indeg[v]+=1
    q=[v for v in nodes if indeg[v]==0]; order=[]
    while q:
        u=q.pop(0); order.append(u)
        for v in succ[u]:
            indeg[v]-=1
            if indeg[v]==0: q.append(v)
    if len(order)!=len(nodes): raise ValueError('cycle')
    return order,pred


def eval_pair(nodes,edges,exactA,postA,Q):
    order,pred=topo(nodes,edges)
    we={}; wp={}; anc={}; bad=[]
    for v in order:
        xe=max((we[u] for u in pred[v]), default=0.0)
        xp=max((wp[u] for u in pred[v]), default=0.0)
        d=postA[v]-exactA[v]
        anc[v]=max([d]+[anc[u] for u in pred[v]])
        we[v]=max(exactA[v],xe+Q[v])
        wp[v]=max(postA[v],xp+Q[v])
        diff=wp[v]-we[v]
        if diff < -1e-10 or diff > anc[v]+1e-10:
            bad.append((v,diff,anc[v]))
    ge=max(we.values(),default=0.0); gp=max(wp.values(),default=0.0)
    md=max((postA[v]-exactA[v] for v in nodes),default=0.0)
    if gp-ge < -1e-10 or gp-ge > md+1e-10:
        bad.append(('global',gp-ge,md))
    return bad, len(nodes)


def edges_for(n,mask):
    poss=[(i,j) for i in range(n) for j in range(i+1,n)]
    return [e for k,e in enumerate(poss) if mask&(1<<k)]


def exhaustive_small():
    sigs=[(0.0,0.0),(1.0,0.0),(1.0,1.0),(2.0,0.0),(2.0,1.0),(2.0,2.0)]
    debts=[0.0,1.0]
    cases=0; node_evals=0; mismatches=[]
    for n in range(1,4):
        nodes=list(range(n)); poss=n*(n-1)//2
        local_choices=[(A,Q,d) for A,Q in sigs for d in debts]
        for mask in range(1<<poss):
            edges=edges_for(n,mask)
            for choice in itertools.product(local_choices, repeat=n):
                exactA={v:choice[v][0] for v in nodes}
                Q={v:choice[v][1] for v in nodes}
                postA={v:choice[v][0]+choice[v][2] for v in nodes}
                bad,ne=eval_pair(nodes,edges,exactA,postA,Q)
                cases+=1; node_evals+=ne
                if bad and len(mismatches)<10:
                    mismatches.append({'n':n,'edges':edges,'choice':choice,'bad':bad})
    return cases,node_evals,mismatches


def rand_envelope(rng,bound=30):
    R=rng.randint(0,bound); Q=rng.randint(0,bound)
    A=rng.randint(max(R,Q),R+Q) if R+Q>=max(R,Q) else max(R,Q)
    return (float(A),float(R),float(Q))


def random_envelope_cases(ncases=50000):
    rng=random.Random(SEED); cases=0; node_evals=0; reversals=0; mismatches=[]
    for _ in range(ncases):
        n=rng.randint(1,8); nodes=list(range(n))
        edges=[(i,j) for i in nodes for j in nodes if i<j and rng.random()<0.22]
        exactA={}; postA={}; Q={}
        for v in nodes:
            z1=rand_envelope(rng); z2=rand_envelope(rng)
            fused=envelope_meet(z1,z2)
            Ae,Qe=deployment_projection(fused)
            Ap=min(z1[0],z2[0]); Qp=min(z1[2],z2[2])
            assert abs(Qe-Qp)<1e-12 and Ae<=Ap+1e-12
            exactA[v]=Ae; postA[v]=Ap; Q[v]=Qe
        bad,ne=eval_pair(nodes,edges,exactA,postA,Q)
        cases+=1; node_evals+=ne
        if bad and len(mismatches)<10:
            mismatches.append({'nodes':nodes,'edges':edges,'exactA':exactA,'postA':postA,'Q':Q,'bad':bad})
        # Count scenarios with at least one grace threshold that changes the binary verdict.
        order,pred=topo(nodes,edges); we={}; wp={}
        for v in order:
            xe=max((we[u] for u in pred[v]),default=0.0)
            xp=max((wp[u] for u in pred[v]),default=0.0)
            we[v]=max(exactA[v],xe+Q[v]); wp[v]=max(postA[v],xp+Q[v])
        if max(wp.values()) > max(we.values()) + 1e-12:
            reversals += 1
    return cases,node_evals,reversals,mismatches


def main():
    ec,en,em=exhaustive_small()
    rc,rn,rev,rm=random_envelope_cases()
    mismatches=em+rm
    out={
        'seed':SEED,
        'exhaustive_small_cases':ec,
        'exhaustive_small_node_evaluations':en,
        'random_envelope_cases':rc,
        'random_envelope_node_evaluations':rn,
        'random_cases_with_nonzero_global_gap':rev,
        'total_cases':ec+rc,
        'total_node_evaluations':en+rn,
        'mismatches':len(mismatches),
        'first_mismatches':mismatches[:10],
        'claim':'For every vertex, early-compression overestimate is bounded by the largest local projection debt among its ancestors; the global gap is bounded by the maximum local debt.'
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    raise SystemExit(1 if mismatches else 0)

if __name__=='__main__': main()
