from copy import deepcopy
from pathlib import Path
import pytest
from model.evidence_model import load_model, compile_view, fuse_views, analyze_sequence
ROOT=Path(__file__).resolve().parents[1]

def test_mokka_machine_readable_model_reproduces_deadline_reversal():
    m=load_model(ROOT/'cases/mokka.json'); out=fuse_views(m,'platform','drain',25)
    assert out['late_fusion_envelope']==(15.0,10.0,5.0)
    assert out['projection_debt_seconds']==15.0
    assert len(out['assumptions'])==1 and 'configured termination grace' in out['assumptions'][0]
    assert out['late_fusion_certified'] is True and out['early_projection_certified'] is False

def test_trino_machine_readable_model_preserves_unknown():
    m=load_model(ROOT/'cases/trino.json'); out=analyze_sequence(m,'worker_shutdown')
    assert out['status']=='Unknown' and out['at_phase']=='active_task_wait'

def test_observation_cannot_be_promoted_to_certificate():
    m=load_model(ROOT/'cases/mokka.json'); m=deepcopy(m)
    m['claims'][0]['kind']='observed_sample_max'
    with pytest.raises(ValueError,match='not certificate-producing'):
        compile_view(m,'platform')

def test_cross_clock_view_is_rejected():
    m=load_model(ROOT/'cases/mokka.json'); m=deepcopy(m)
    m['claims'][1]['clock']='runtime-wall-clock'
    with pytest.raises(ValueError,match='different clocks'):
        compile_view(m,'platform')


def test_assumption_scoped_completion_requires_declared_assumption():
    m=load_model(ROOT/'cases/mokka.json'); m=deepcopy(m)
    m['claims'][0].pop('assumption',None)
    with pytest.raises(ValueError,match='explicit analysis assumption'):
        compile_view(m,'platform')
