"""Configuration-grounded examples used in the manuscript.

These functions intentionally operate on declared configuration semantics.
They do not claim scheduler-inclusive wall-clock guarantees for Kubernetes or
Trino. Provenance and semantic scope are recorded under provenance/.
"""
from __future__ import annotations

from .timing_abstraction import (
    canonical_envelope_from_caps,
    deployment_projection,
    envelope_meet,
    projection_debt,
    meet,
)


def mokka_configuration_case():
    """Return the Mokka configuration-clock calculation from Sec. 3.2.

    Platform evidence: a 30-s assumption-scoped configuration horizon and
    a 10-s declared lifecycle-delay coordinate. Application evidence: a 5-s
    drain-wait budget.
    """
    platform = canonical_envelope_from_caps(30, 10, 30)
    drain = canonical_envelope_from_caps(30, 30, 5)
    exact = envelope_meet(platform, drain)
    exact_deployment = deployment_projection(exact)
    early = meet(deployment_projection(platform), deployment_projection(drain))
    debt = projection_debt(platform, drain)
    return {
        "semantic_scope": "closed declared configuration clock; not a wall-clock runtime SLA",
        "analysis_assumption": "the configured termination grace is treated as the model horizon; documented extension and scheduler/runtime effects are outside the model",
        "platform_envelope": platform,
        "drain_envelope": drain,
        "late_fusion_envelope": exact,
        "late_fusion_deployment": exact_deployment,
        "early_projection_deployment": early,
        "projection_debt_seconds": debt,
    }


def trino_configuration_case(active_task_completion_cap=None):
    """Conservatively represent the Trino graceful-shutdown documentation.

    The cited procedure has two fixed grace-period sleeps separated by a wait
    until active tasks complete. Without a separately justified finite cap
    for that intervening wait, no finite complete-shutdown certificate is
    emitted. If a caller supplies such a cap, the function reports only the
    arithmetic configuration-model sum; source provenance for that extra cap is
    the caller's responsibility.
    """
    grace = 120.0
    if active_task_completion_cap is None:
        return {
            "status": "Unknown",
            "grace_period_seconds": grace,
            "reason": "no finite upper bound for the active-task completion wait in the cited source contract",
        }
    cap = float(active_task_completion_cap)
    if cap < 0:
        raise ValueError("active_task_completion_cap must be non-negative")
    return {
        "status": "Finite only with external evidence",
        "grace_period_seconds": grace,
        "active_task_completion_cap_seconds": cap,
        "configuration_model_completion_cap_seconds": 2 * grace + cap,
    }
