from model.timing_abstraction import alpha, gamma_contains, refines, join, meet


def test_galois_membership_characterization_on_finite_contract():
    S={(0,2),(3,0),(1,1)}
    a=alpha(S)
    assert a==(3.0,2.0)
    assert all(gamma_contains(a,p) for p in S)
    assert refines(alpha({(0,1)}),a)


def test_union_join_and_optimal_signature_meet_example():
    S={(0,2),(3,0)}; T={(1,2),(3,0)}
    assert alpha(S|T)==join(alpha(S),alpha(T))
    assert meet(alpha(S),alpha(T))==(3.0,2.0)
    assert alpha(S&T)==(3.0,0.0)  # exact intersection can be tighter


def test_unbounded_signature_only_fusion_family_at_M_32():
    M=32
    S={(0,M),(0,1)}; T={(M,0),(0,1)}
    m=meet(alpha(S),alpha(T))
    exact=alpha(S&T)
    assert m==(32.0,1.0)
    assert exact==(1.0,1.0)
    assert m[0]/exact[0]==32.0
