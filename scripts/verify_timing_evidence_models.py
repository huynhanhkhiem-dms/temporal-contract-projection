#!/usr/bin/env python3
"""End-to-end verification of the machine-readable evidence models."""
from __future__ import annotations
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from model.evidence_model import load_model, fuse_views, analyze_sequence

def main():
    mokka=load_model(ROOT/'cases/mokka.json'); trino=load_model(ROOT/'cases/trino.json')
    mo=fuse_views(mokka,'platform','drain',25); tr=analyze_sequence(trino,'worker_shutdown')
    checks={
      'mokka_exact_envelope':mo['late_fusion_envelope']==(15.0,10.0,5.0),
      'mokka_projection_debt':mo['projection_debt_seconds']==15.0,
      'mokka_decision_reversal':mo['late_fusion_certified'] and not mo['early_projection_certified'],
      'trino_unknown':tr['status']=='Unknown' and tr['at_phase']=='active_task_wait',
    }
    out={'verifier':'timing_evidence_models','checks':checks,'mismatches':sum(not v for v in checks.values()),'mokka':mo,'trino':tr}
    (ROOT/'outputs/timing_evidence_model_checks.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(1 if out['mismatches'] else 0)
if __name__=='__main__': main()
