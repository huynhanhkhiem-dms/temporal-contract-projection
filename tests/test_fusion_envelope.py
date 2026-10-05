from model.timing_abstraction import (
    alpha, envelope_alpha, envelope_contains, envelope_meet,
    envelope_meet_many, deployment_projection, projection_debt,
    projection_debt_many, compression_commutes, canonical_envelope_from_caps,
)


def test_envelope_abstraction_and_projection():
    S={(0,4),(3,0),(2,1)}
    z=envelope_alpha(S)
    assert z==(4.0,3.0,4.0)
    assert all(envelope_contains(z,p) for p in S)
    assert deployment_projection(z)==alpha(S)==(4.0,4.0)


def test_reduced_meet_recovers_hidden_release_cap_precision():
    # Coordinatewise minimum would be the invalid triple (10,0,0).
    a=(10.0,10.0,0.0)
    b=(10.0,0.0,10.0)
    assert envelope_meet(a,b)==(0.0,0.0,0.0)
    assert deployment_projection(envelope_meet(a,b))==(0.0,0.0)
    assert projection_debt(a,b)==10.0


def test_release_cap_is_observationally_necessary_for_future_fusion():
    # Same deployment interface (A,Q), different release cap R.
    A,Q=10.0,6.0
    narrow=(A,5.0,Q)
    wide=(A,8.0,Q)
    probe=(A,A,A-wide[1])  # Q_probe=A-R_wide=2
    fused_narrow=deployment_projection(envelope_meet(narrow,probe))
    fused_wide=deployment_projection(envelope_meet(wide,probe))
    assert deployment_projection(narrow)==deployment_projection(wide)==(A,Q)
    assert fused_narrow==(7.0,2.0)
    assert fused_wide==(10.0,2.0)


def test_n_way_reduced_meet_and_debt_formula():
    zs=[(9.0,7.0,5.0),(8.0,3.0,6.0),(10.0,8.0,2.0)]
    # min A=8, min R=3, min Q=2 => reduced A=min(8,5)=5
    z=envelope_meet_many(zs)
    assert z==(5.0,3.0,2.0)
    assert deployment_projection(z)==(5.0,2.0)
    assert projection_debt(zs[0],zs[2])==0.0
    assert projection_debt_many(zs)==3.0
    assert not compression_commutes(zs)
    assert compression_commutes([(8.0,6.0,4.0),(7.0,5.0,4.0)])


def test_identity_probe_recovers_deployment_coordinates():
    z=(7.0,5.0,4.0)
    top=(10.0,10.0,10.0)
    assert envelope_meet(z,top)==z
    assert deployment_projection(envelope_meet(z,top))==(7.0,4.0)


def test_zero_duration_probe_exposes_release_coordinate():
    z=(7.0,5.0,4.0)
    release_probe=(10.0,10.0,0.0)
    assert deployment_projection(envelope_meet(z,release_probe))==(5.0,0.0)


def test_fusion_deployment_context_order_needs_all_three_coordinates():
    z1=(8.0,4.0,5.0)
    z2=(8.0,6.0,5.0)
    assert deployment_projection(z1)==deployment_projection(z2)==(8.0,5.0)
    probe=(8.0,8.0,2.0)
    assert deployment_projection(envelope_meet(z1,probe))==(6.0,2.0)
    assert deployment_projection(envelope_meet(z2,probe))==(8.0,2.0)


def test_raw_cap_canonicalization_removes_redundancy():
    assert canonical_envelope_from_caps(30, 100, 100) == (30.0, 30.0, 30.0)
    assert canonical_envelope_from_caps(100, 10, 10) == (20.0, 10.0, 10.0)
    assert canonical_envelope_from_caps(10, 3, 9) == (10.0, 3.0, 9.0)


def test_conservative_caps_contain_true_timing_points():
    true_points={(2.0,3.0),(5.0,1.0),(0.0,2.0)}
    loose=canonical_envelope_from_caps(10,8,9)
    assert all(envelope_contains(loose,p) for p in true_points)
    assert alpha(true_points)[0] <= deployment_projection(loose)[0]
    assert alpha(true_points)[1] <= deployment_projection(loose)[1]


def test_tightening_valid_caps_monotonically_improves_fused_certificate():
    loose=canonical_envelope_from_caps(12,10,8)
    tight=canonical_envelope_from_caps(8,6,4)
    probe=(7.0,5.0,3.0)
    fused_loose=envelope_meet(loose,probe)
    fused_tight=envelope_meet(tight,probe)
    # Tightened evidence denotes a subset and cannot worsen deployment bounds.
    assert fused_tight[0] <= fused_loose[0]
    assert fused_tight[1] <= fused_loose[1]
    assert fused_tight[2] <= fused_loose[2]
    assert deployment_projection(fused_tight)[0] <= deployment_projection(fused_loose)[0]
    assert deployment_projection(fused_tight)[1] <= deployment_projection(fused_loose)[1]


def test_projection_debt_does_not_accumulate_along_chain():
    from model.structure_oracle import projection_debt_propagation
    nodes=['a','b','c']; edges=[('a','b'),('b','c')]
    exact_A={'a':20.0,'b':20.0,'c':20.0}
    post_A={'a':30.0,'b':30.0,'c':30.0}
    Q={'a':10.0,'b':10.0,'c':10.0}
    out=projection_debt_propagation(nodes,edges,exact_A,post_A,Q)
    assert out['W_exact']=={'a':20.0,'b':30.0,'c':40.0}
    assert out['W_post']=={'a':30.0,'b':40.0,'c':50.0}
    assert out['global_overestimate']==10.0
    assert out['max_local_debt']==10.0


def test_projection_debt_ancestor_localization_on_branch():
    from model.structure_oracle import projection_debt_propagation
    nodes=['a','b','c','d']; edges=[('a','c'),('b','c'),('c','d')]
    exact_A={'a':6.0,'b':8.0,'c':5.0,'d':4.0}
    post_A={'a':8.0,'b':15.0,'c':8.0,'d':5.0}
    Q={'a':2.0,'b':1.0,'c':3.0,'d':2.0}
    out=projection_debt_propagation(nodes,edges,exact_A,post_A,Q)
    assert out['local_debt']=={'a':2.0,'b':7.0,'c':3.0,'d':1.0}
    assert out['ancestor_max_debt']['d']==7.0
    for v in nodes:
        assert 0 <= out['W_post'][v]-out['W_exact'][v] <= out['ancestor_max_debt'][v] + 1e-12


def test_deadline_reversal_window_is_bounded_by_max_local_projection_debt():
    from model.structure_oracle import projection_debt_propagation
    nodes=['a','b']; edges=[('a','b')]
    exact_A={'a':20.0,'b':20.0}; post_A={'a':30.0,'b':30.0}; Q={'a':10.0,'b':10.0}
    out=projection_debt_propagation(nodes,edges,exact_A,post_A,Q)
    # Exact completion is 30 and early-compression completion is 40.
    # Any grace that reverses the verdict lies in [30,40), a width of 10,
    # exactly the largest local projection debt rather than the sum 20.
    assert out['exact_global']==30.0 and out['post_global']==40.0
    assert out['post_global']-out['exact_global'] <= out['max_local_debt']
    assert out['max_local_debt']==10.0
