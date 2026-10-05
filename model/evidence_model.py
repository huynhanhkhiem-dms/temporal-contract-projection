"""Typed timing-evidence model used by the manuscript case studies.

The analyzer distinguishes certificate-producing evidence from observations,
SLO targets, and explicitly unknown bounds. It uses only Python's standard
library so the supplementary artifact remains easy to reproduce.
"""
from __future__ import annotations
import json
from pathlib import Path
from .timing_abstraction import canonical_envelope_from_caps, envelope_meet, deployment_projection, meet, projection_debt

CERT_KINDS={"completion_upper","assumed_completion_upper","release_upper","release_exact","duration_upper","duration_exact"}
NONCERT_KINDS={"observed_sample_max","slo_target"}
UNKNOWN_KINDS={"unknown_completion","unknown_release","unknown_duration"}

def load_model(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _claims(model):
    return {c["id"]:c for c in model.get("claims",[])}

def _claim(model, cid):
    c=_claims(model)[cid]
    if not c.get("provenance"): raise ValueError(f"claim {cid} lacks provenance")
    if c["kind"] in NONCERT_KINDS: raise ValueError(f"claim {cid} is not certificate-producing evidence")
    if c["kind"]=="assumed_completion_upper" and not c.get("assumption"):
        raise ValueError(f"claim {cid} requires an explicit analysis assumption")
    if c["kind"] in UNKNOWN_KINDS: return None
    if c["kind"] not in CERT_KINDS: raise ValueError(f"unsupported evidence kind: {c['kind']}")
    v=float(c["value_seconds"]);
    if v<0: raise ValueError("timing values must be non-negative")
    return c

def compile_view(model, view_name):
    view=model["views"][view_name]; ids=view["claims"]; cs=[_claim(model,i) for i in ids]
    if any(c is None for c in cs): return {"status":"Unknown","reason":"required view contains an explicitly unknown bound"}
    clocks={c["clock"] for c in cs}
    if len(clocks)!=1: raise ValueError("cannot fuse claims from different clocks without an explicit clock mapping")
    vals={"A":None,"R":None,"Q":None}; completion=None
    for c in cs:
        k=c["kind"]; v=float(c["value_seconds"])
        if k in {"completion_upper","assumed_completion_upper"}: completion=v if completion is None else min(completion,v)
    if completion is None: return {"status":"Unknown","reason":"view has no completion upper bound"}
    vals["A"]=completion; vals["R"]=completion; vals["Q"]=completion
    for c in cs:
        k=c["kind"]; v=float(c["value_seconds"])
        if k in {"release_upper","release_exact"}: vals["R"]=min(vals["R"],v)
        elif k in {"duration_upper","duration_exact"}: vals["Q"]=min(vals["Q"],v)
    z=canonical_envelope_from_caps(vals["A"],vals["R"],vals["Q"])
    assumptions=[c["assumption"] for c in cs if c["kind"]=="assumed_completion_upper"]
    return {"status":"Finite","clock":next(iter(clocks)),"envelope":z,"deployment":deployment_projection(z),"assumptions":assumptions}

def fuse_views(model, left, right, deadline_seconds=None):
    l=compile_view(model,left); r=compile_view(model,right)
    if l["status"]!="Finite" or r["status"]!="Finite": return {"status":"Unknown"}
    if l["clock"]!=r["clock"]: raise ValueError("cannot fuse views on different clocks")
    exact_z=envelope_meet(l["envelope"],r["envelope"]); exact=deployment_projection(exact_z)
    early=meet(l["deployment"],r["deployment"]); debt=projection_debt(l["envelope"],r["envelope"])
    out={"status":"Finite","late_fusion_envelope":exact_z,"late_fusion_deployment":exact,"early_projection_deployment":early,"projection_debt_seconds":debt,"assumptions":list(dict.fromkeys(l.get("assumptions",[])+r.get("assumptions",[])))}
    if deadline_seconds is not None:
        g=float(deadline_seconds); out["deadline_seconds"]=g; out["late_fusion_certified"]=exact[0]<=g; out["early_projection_certified"]=early[0]<=g
    return out

def analyze_sequence(model, sequence_name):
    seq=model["sequences"][sequence_name]; total=0.0
    for cid in seq["phases"]:
        c=_claim(model,cid)
        if c is None: return {"status":"Unknown","at_phase":cid,"reason":"no finite upper bound for required phase"}
        if c["kind"] not in {"duration_upper","duration_exact"}: raise ValueError("sequential phase requires duration evidence")
        total += float(c["value_seconds"])
    return {"status":"Finite","completion_cap_seconds":total}
