#!/usr/bin/env python3
"""Reproduce the two configuration-grounded case calculations."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model.configuration_cases import mokka_configuration_case, trino_configuration_case


def lists(obj):
    if isinstance(obj, tuple):
        return [lists(x) for x in obj]
    if isinstance(obj, dict):
        return {k: lists(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [lists(x) for x in obj]
    return obj


def main():
    mokka = mokka_configuration_case()
    trino = trino_configuration_case()
    assert mokka["late_fusion_envelope"] == (15.0, 10.0, 5.0)
    assert mokka["late_fusion_deployment"] == (15.0, 5.0)
    assert mokka["early_projection_deployment"] == (30.0, 5.0)
    assert mokka["projection_debt_seconds"] == 15.0
    assert trino["status"] == "Unknown"
    result = {
        "verifier": "configuration_cases",
        "mismatches": 0,
        "mokka": lists(mokka),
        "trino": lists(trino),
        "note": "Mokka result is conditional on the explicit closed configuration-clock assumption; it is not a scheduler-inclusive runtime measurement or SLA.",
    }
    out = ROOT / "outputs" / "configuration_case_checks.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
