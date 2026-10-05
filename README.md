# Temporal Contract Projection

Reproducibility artifact for the manuscript **“Provenance-Aware Shutdown Timing Analysis: Exact Abstraction, Evidence Fusion, and Projection Debt.”**

This repository implements the timing-evidence model, projection/fusion operations, case models, regression tests, and verification programs used in the paper. The mathematical proofs in the manuscript are primary; the executable checks are regression and falsification aids and reproducibility support.

## Scope

The artifact studies operator-relative abstraction of shutdown timing evidence under acyclic precedence. It includes:

- deployment abstraction `(A,Q)` and fusion-complete envelope `(A,R,Q)`;
- exact envelope conjunction and projection-debt calculations;
- provenance-aware timing-evidence models;
- a Kubernetes/NVIDIA Mokka configuration case;
- a Trino graceful-shutdown case that intentionally returns `Unknown` when a finite active-task bound is absent;
- regression tests and executable verification programs.

The Mokka result is a **conditional configuration-model certificate**, not a scheduler-inclusive wall-clock shutdown guarantee. The 30 s horizon is used only under the explicit closed-configuration-clock assumption encoded in the case model.

## Repository layout

- `model/` — timing abstractions, recurrence logic, evidence model, and configuration-case helpers.
- `cases/` — machine-readable Mokka and Trino case models.
- `schema_timing_evidence.json` — JSON Schema for the timing-evidence model.
- `scripts/analyze_case.py` — command-line case analyzer.
- `scripts/verify_*.py` — executable verification programs.
- `tests/` — regression suite.
- `outputs/` — generated JSON outputs from the verification programs.
- `provenance/` — pinned public source metadata used by the configuration cases.

## Requirements

Python 3.11 or later.

```bash
python -m pip install -r requirements.txt
```

## Reproduce the regression suite

```bash
python -m pytest -q
```

Expected result: **28 passed**.

## Run the configuration cases

```bash
python scripts/analyze_case.py cases/mokka.json
python scripts/analyze_case.py cases/trino.json --sequence worker_shutdown
```

The Mokka case reports late fusion `(15,10,5)`, early deployment projection `(30,5)`, and projection debt of 15 s. The Trino sequence reports `Unknown` at the active-task wait because the cited source contract provides no finite upper bound for that phase.

## Run the verification programs

```bash
python scripts/verify_general_timing_signature.py
python scripts/verify_signature_algebra.py
python scripts/verify_abstract_domain.py
python scripts/verify_projection_complete_envelope.py
python scripts/verify_operation_relative_contexts.py
python scripts/verify_projection_debt_propagation.py
python scripts/verify_coupled_contract.py
python scripts/verify_coupled_extreme_random.py
python scripts/verify_configuration_cases.py
python scripts/verify_timing_evidence_models.py
```

Each program should terminate successfully and report zero mismatches.

## Provenance

Third-party source trees are not redistributed. The case models and `provenance/configuration_sources.json` record public URLs, repository paths, immutable commits where available, and access dates.

## Author

Huynh Anh Khiem  
Faculty of Information Technology, Ton Duc Thang University, Ho Chi Minh City, Vietnam  
ORCID: 0009-0007-7210-174X
