"""Generic precedence-graph oracles for operation-relative timing interfaces.

The implementation is intentionally separated from platform-specific
lifecycle. Nodes form a finite acyclic precedence graph. Each timed node has a
non-negative release offset r and duration d.
"""
from __future__ import annotations
from collections import deque


def _topological(nodes, edges):
    nodes=list(nodes)
    succ={v:[] for v in nodes}; indeg={v:0 for v in nodes}
    for u,v in edges:
        if u not in succ or v not in succ:
            raise ValueError('edge references unknown node')
        succ[u].append(v); indeg[v]+=1
    q=deque(v for v in nodes if indeg[v]==0)
    order=[]
    while q:
        u=q.popleft(); order.append(u)
        for v in succ[u]:
            indeg[v]-=1
            if indeg[v]==0: q.append(v)
    if len(order)!=len(nodes):
        raise ValueError('graph contains a cycle')
    return order,succ


def dag_completion_time(nodes, edges, release, duration):
    """Evaluate C[v]=max(r[v], max_pred C)+d[v] on an acyclic graph."""
    nodes=list(nodes); order,_=_topological(nodes,edges)
    pred={v:[] for v in nodes}
    for u,v in edges: pred[v].append(u)
    C={}
    for v in order:
        r=float(release.get(v,0.0)); d=float(duration.get(v,0.0))
        if r<0 or d<0: raise ValueError('release and duration must be non-negative')
        x=max((C[u] for u in pred[v]),default=0.0)
        C[v]=max(r,x)+d
    return max(C.values(),default=0.0),C


def timing_signature_from_points(points):
    """Return the deployment signature (A,Q) of a finite timing set."""
    pts=list(points)
    if not pts: raise ValueError('timing set must be non-empty')
    if any(float(r)<0 or float(d)<0 for r,d in pts):
        raise ValueError('release and duration must be non-negative')
    return (max(float(r)+float(d) for r,d in pts), max(float(d) for _,d in pts))


def signature_upper(nodes, edges, isolated_completion_caps, duration_caps, timed_nodes=None):
    """Exact robust completion from local (A,Q) signatures."""
    nodes=list(nodes); timed=set(nodes if timed_nodes is None else timed_nodes)
    if not timed.issubset(nodes): raise ValueError('timed_nodes contains unknown node')
    order,_=_topological(nodes,edges)
    pred={v:[] for v in nodes}
    for u,v in edges: pred[v].append(u)
    W={}
    for v in order:
        x=max((W[u] for u in pred[v]),default=0.0)
        if v not in timed:
            W[v]=x; continue
        A=float(isolated_completion_caps[v]); Q=float(duration_caps[v])
        if A<0 or Q<0 or Q>A+1e-12:
            raise ValueError('signature must satisfy 0 <= Q <= A')
        W[v]=max(A,x+Q)
    return max(W.values(),default=0.0),W


def projection_debt_propagation(nodes, edges, exact_A, post_A, duration_caps, timed_nodes=None):
    """Check the ancestor-local non-amplification bound for projection debt."""
    nodes=list(nodes); timed=set(nodes if timed_nodes is None else timed_nodes)
    if not timed.issubset(nodes): raise ValueError('timed_nodes contains unknown node')
    order,_=_topological(nodes,edges)
    pred={v:[] for v in nodes}
    for u,v in edges: pred[v].append(u)
    W_exact={}; W_post={}; local_debt={}; ancestor_max_debt={}
    for v in order:
        xe=max((W_exact[u] for u in pred[v]),default=0.0)
        xp=max((W_post[u] for u in pred[v]),default=0.0)
        inherited=max((ancestor_max_debt[u] for u in pred[v]),default=0.0)
        if v not in timed:
            W_exact[v]=xe; W_post[v]=xp; local_debt[v]=0.0; ancestor_max_debt[v]=inherited
            continue
        Ae=float(exact_A[v]); Ap=float(post_A[v]); Q=float(duration_caps[v])
        if Q<0 or Ae<0 or Ap<0 or Q>Ae+1e-12 or Ae>Ap+1e-12:
            raise ValueError('projection signatures must satisfy 0 <= Q <= exact_A <= post_A')
        debt=max(0.0,Ap-Ae)
        local_debt[v]=debt; ancestor_max_debt[v]=max(inherited,debt)
        W_exact[v]=max(Ae,xe+Q); W_post[v]=max(Ap,xp+Q)
        diff=W_post[v]-W_exact[v]
        if diff < -1e-10 or diff > ancestor_max_debt[v]+1e-10:
            raise AssertionError('projection debt propagation bound violated')
    exact_global=max(W_exact.values(),default=0.0); post_global=max(W_post.values(),default=0.0)
    delta=post_global-exact_global; max_debt=max(local_debt.values(),default=0.0)
    if delta < -1e-10 or delta > max_debt+1e-10:
        raise AssertionError('global projection debt propagation bound violated')
    return {'exact_global':exact_global,'post_global':post_global,'global_overestimate':delta,
            'max_local_debt':max_debt,'W_exact':W_exact,'W_post':W_post,
            'local_debt':local_debt,'ancestor_max_debt':ancestor_max_debt}


def coupled_contract_signature(release_cap, duration_cap, end_to_end_cap):
    """Deployment signature of 0<=r<=R, 0<=d<=D, r+d<=B."""
    R=float(release_cap); D=float(duration_cap); B=float(end_to_end_cap)
    if R<0 or D<0 or B<0: raise ValueError('contract values must be non-negative')
    return min(B,R+D), min(B,D)


def sharp_contract_upper(nodes, edges, release_caps, duration_caps, end_to_end_caps, timed_nodes=None):
    """Exact robust completion for coupled three-cap local contracts."""
    nodes=list(nodes); timed=set(nodes if timed_nodes is None else timed_nodes)
    if not timed.issubset(nodes): raise ValueError('timed_nodes contains unknown node')
    A={}; Q={}
    for v in timed:
        A[v],Q[v]=coupled_contract_signature(release_caps[v],duration_caps[v],end_to_end_caps[v])
    return signature_upper(nodes,edges,A,Q,timed)
