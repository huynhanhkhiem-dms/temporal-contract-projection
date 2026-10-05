#!/usr/bin/env python3
"""Finite brute-force regression for the sharp coupled-contract recurrence."""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from model.structure_oracle import sharp_contract_upper
from model.structure_oracle import dag_completion_time

GRID=(0.0,0.5,1.0)
CONTRACTS=((1.0,1.0,1.0),(0.5,1.0,1.0),(1.0,0.5,1.0),(0.5,0.5,1.0),(1.0,1.0,0.5),(0.5,1.0,0.5))

def ordered_dags(n):
    poss=[(i,j) for i in range(n) for j in range(i+1,n)]
    for mask in range(1<<len(poss)):
        yield [e for k,e in enumerate(poss) if mask&(1<<k)]

def local_realizations(R,D,b):
    return [(r,d) for r in GRID for d in GRID if r<=R+1e-12 and d<=D+1e-12 and r+d<=b+1e-12]

def main():
    contract_cases=0; realization_evals=0; mismatches=[]; dags=0
    for n in range(1,4):
        nodes=list(range(n))
        for edges in ordered_dags(n):
            dags += 1
            for cs in itertools.product(CONTRACTS, repeat=n):
                contract_cases += 1
                R={i:cs[i][0] for i in nodes}; D={i:cs[i][1] for i in nodes}; b={i:cs[i][2] for i in nodes}
                predicted,_=sharp_contract_upper(nodes,edges,R,D,b)
                observed=-1.0
                local=[local_realizations(*cs[i]) for i in nodes]
                for vals in itertools.product(*local):
                    release={i:vals[i][0] for i in nodes}; duration={i:vals[i][1] for i in nodes}
                    t,_=dag_completion_time(nodes,edges,release,duration)
                    realization_evals += 1
                    observed=max(observed,t)
                if abs(predicted-observed)>1e-12 and len(mismatches)<10:
                    mismatches.append({'n':n,'edges':edges,'contracts':cs,'predicted':predicted,'observed':observed})
    out={'n_max':3,'dags':dags,'contract_cases':contract_cases,'realization_evaluations':realization_evals,
         'grid':GRID,'contract_templates':CONTRACTS,'mismatches':len(mismatches),'examples':mismatches,
         'note':'Finite grid regression only; theorem is proved analytically.'}
    p=ROOT/'outputs/coupled_contract_exhaustive.json'; p.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    raise SystemExit(1 if mismatches else 0)
if __name__=='__main__': main()
