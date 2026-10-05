#!/usr/bin/env python3
"""Randomized cross-check of the coupled-contract recurrence.

For each random DAG (up to 5 nodes), generate random coupled local contract
polytopes. Independently enumerate every Cartesian product of local polygon
vertices and evaluate the original DAG completion recurrence. Compare the
observed maximum against sharp_contract_upper. This does not use the coupled
recurrence to construct realizations, so it does not use the coupled closed-form
falsification search for small instances.
"""
from __future__ import annotations
import itertools, json, random, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from model.structure_oracle import sharp_contract_upper
from model.structure_oracle import dag_completion_time

SEED=20260914
RNG=random.Random(SEED)
N_CASES=2500


def random_dag(n, p=0.35):
    return [(i,j) for i in range(n) for j in range(i+1,n) if RNG.random()<p]


def vertices(R,D,b):
    # Candidate intersections of r=0/R, d=0/D, r+d=b.
    cand={(0.0,0.0),(min(R,b),0.0),(0.0,min(D,b))}
    lines_r=[0.0,R]
    lines_d=[0.0,D]
    for r in lines_r:
        cand.add((r,0.0)); cand.add((r,D)); cand.add((r,b-r))
    for d in lines_d:
        cand.add((0.0,d)); cand.add((R,d)); cand.add((b-d,d))
    out=[]
    for r,d in cand:
        if r>=-1e-10 and d>=-1e-10 and r<=R+1e-10 and d<=D+1e-10 and r+d<=b+1e-10:
            out.append((max(0.0,r),max(0.0,d)))
    # Rounded de-duplication for stable enumeration.
    uniq=sorted({(round(r,10),round(d,10)) for r,d in out})
    return uniq


def main():
    mismatches=[]; realization_evals=0; by_n={}; max_vertex_product=0
    for case in range(N_CASES):
        n=RNG.randint(1,5); nodes=list(range(n)); edges=random_dag(n)
        R={}; D={}; b={}; local=[]
        for v in nodes:
            # Log-spread values, then round to keep exact-ish decimal vertices.
            rv=round(10**RNG.uniform(-1.0,0.7),3)
            dv=round(10**RNG.uniform(-1.0,0.7),3)
            bv=round(10**RNG.uniform(-1.0,0.7),3)
            R[v]=rv; D[v]=dv; b[v]=bv
            local.append(vertices(rv,dv,bv))
        prod=1
        for xs in local: prod*=len(xs)
        max_vertex_product=max(max_vertex_product,prod)
        predicted,_=sharp_contract_upper(nodes,edges,R,D,b)
        observed=-1.0
        for vals in itertools.product(*local):
            release={v:vals[v][0] for v in nodes}; duration={v:vals[v][1] for v in nodes}
            t,_=dag_completion_time(nodes,edges,release,duration)
            realization_evals += 1
            if t>observed: observed=t
        by_n[str(n)]=by_n.get(str(n),0)+1
        if abs(predicted-observed)>1e-8 and len(mismatches)<20:
            mismatches.append({'case':case,'n':n,'edges':edges,'R':R,'D':D,'b':b,
                               'predicted':predicted,'observed':observed,'vertex_product':prod})
    out={'seed':SEED,'random_cases':N_CASES,'nodes_max':5,'by_n':by_n,
         'extreme_point_realization_evaluations':realization_evals,
         'max_vertex_product':max_vertex_product,'mismatch_count':len(mismatches),
         'mismatches':mismatches,
         'note':'Finite falsification search: enumerates local-polytope vertices and evaluates the original completion recurrence rather than the closed-form coupled recurrence.'}
    p=ROOT/'outputs/coupled_contract_random_extreme.json'; p.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    raise SystemExit(1 if mismatches else 0)
if __name__=='__main__': main()
