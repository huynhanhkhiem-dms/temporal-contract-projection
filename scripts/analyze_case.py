#!/usr/bin/env python3
"""Command-line entry point for the released timing-evidence case models."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model.evidence_model import load_model, fuse_views, analyze_sequence

def main():
    ap = argparse.ArgumentParser(description='Analyze a timing-evidence JSON model.')
    ap.add_argument('model', type=Path)
    ap.add_argument('--view-left')
    ap.add_argument('--view-right')
    ap.add_argument('--sequence')
    ap.add_argument('--deadline', type=float)
    args = ap.parse_args()
    model = load_model(args.model)
    if args.sequence:
        out = analyze_sequence(model, args.sequence)
    elif args.view_left and args.view_right:
        out = fuse_views(model, args.view_left, args.view_right, args.deadline)
    else:
        cfg = model.get('analysis', {})
        if 'fuse' in cfg:
            left, right = cfg['fuse']
            out = fuse_views(model, left, right, cfg.get('deadline_seconds'))
        elif model.get('sequences'):
            name = next(iter(model['sequences']))
            out = analyze_sequence(model, name)
        else:
            raise SystemExit('model contains neither a fusion analysis nor a sequence')
    print(json.dumps(out, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
