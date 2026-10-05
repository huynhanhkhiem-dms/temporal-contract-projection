from model.structure_oracle import timing_signature_from_points, signature_upper


def test_general_timing_signature_recurrence_on_nonconvex_sets():
    nodes=['a','b']; edges=[('a','b')]
    Sa=[(5,0),(0,5),(2,1)]; Sb=[(1,1),(0,3),(3,0)]
    Aa,Qa=timing_signature_from_points(Sa); Ab,Qb=timing_signature_from_points(Sb)
    total,_=signature_upper(nodes,edges,{'a':Aa,'b':Ab},{'a':Qa,'b':Qb})
    brute=[]
    for ra,da in Sa:
        ca=ra+da
        for rb,db in Sb:
            brute.append(max(ca,max(rb,ca)+db))
    assert total==max(brute)


def test_timing_signature_contextual_separation_examples():
    s_release=[(5,0)]; s_duration=[(0,5)]
    assert timing_signature_from_points(s_release)==(5.0,0.0)
    assert timing_signature_from_points(s_duration)==(5.0,5.0)
    nodes=['p','v']; edges=[('p','v')]
    t1,_=signature_upper(nodes,edges,{'p':10,'v':5},{'p':0,'v':0})
    t2,_=signature_upper(nodes,edges,{'p':10,'v':5},{'p':0,'v':5})
    assert t1==10 and t2==15


def test_signature_conjunction_is_not_identifiable_from_signatures_alone():
    P={(0,2),(3,0)}; R={(1,2),(3,0)}
    assert timing_signature_from_points(P)==timing_signature_from_points(R)==(3.0,2.0)
    assert timing_signature_from_points(P & P)==(3.0,2.0)
    assert timing_signature_from_points(P & R)==(3.0,0.0)
