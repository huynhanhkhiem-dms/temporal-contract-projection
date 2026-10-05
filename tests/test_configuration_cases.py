from model.configuration_cases import mokka_configuration_case, trino_configuration_case


def test_mokka_configuration_case_late_fusion():
    case = mokka_configuration_case()
    assert case["platform_envelope"] == (30.0, 10.0, 30.0)
    assert case["drain_envelope"] == (30.0, 30.0, 5.0)
    assert case["late_fusion_envelope"] == (15.0, 10.0, 5.0)
    assert case["late_fusion_deployment"] == (15.0, 5.0)


def test_mokka_configuration_case_early_projection_debt():
    case = mokka_configuration_case()
    assert case["early_projection_deployment"] == (30.0, 5.0)
    assert case["projection_debt_seconds"] == 15.0


def test_trino_without_active_task_cap_remains_unknown():
    case = trino_configuration_case()
    assert case["status"] == "Unknown"
    assert "no finite upper bound" in case["reason"]


def test_trino_finite_result_requires_explicit_external_cap():
    case = trino_configuration_case(active_task_completion_cap=60)
    assert case["status"] == "Finite only with external evidence"
    assert case["configuration_model_completion_cap_seconds"] == 300.0
