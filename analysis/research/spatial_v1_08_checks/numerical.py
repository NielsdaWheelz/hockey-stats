"""temporary independent numerical acceptance checks for v1-08."""
from itertools import permutations
import math
import numpy as np
from scipy.sparse import csr_matrix
from scipy.special import expit, logsumexp
from types import SimpleNamespace

from hockey_stats.spatial_rates import head_objective, annual_priors, evaluate_rates, centered_reference, spatial_shapley


def tiny_design():
    rng = np.random.default_rng(281)
    basis = rng.normal(size=(656, 40))
    basis -= basis.mean(axis=0)
    basis = np.linalg.qr(basis)[0] * math.sqrt(656)
    x = np.array([[1., 1., 0., -.5], [1., 0., 1., .5]])
    cells = np.array([3, 90, 32], dtype=np.int64)
    o = np.array([.3, .7, 1.])
    return SimpleNamespace(season='20232024',purpose='fixture',columns=(
        {'kind':'intercept','name':'intercept'},
        {'kind':'actor','name':'a','block':'attacking_player','id':'1','subblock':'base'},
        {'kind':'actor','name':'b','block':'attacking_player','id':'2','subblock':'base'},
        {'kind':'context','name':'ctx'}), players=('1','2','3'),
        player_facts={str(i):{'position_group':'F','age_days':27*365.2425} for i in (1,2,3)},
        X_time=csr_matrix(x[:,:3]), X_event=csr_matrix(x[:,:3]),context_time=x[:,3:],context_event=x[:,3:],exposure_hours=np.array([.25,.75]),
        event_offsets=np.array([0,2,3],dtype=np.int64),origin_cells=cells,origin_weights=o,
        neutral_goal_probability=np.array([0.,.1,1.]), basis=basis,
        annual_offsets={'r':3.,'pi':np.full(656,1/656).tolist(),'qbar':np.full(656,.15).tolist()})


def main():
    d=tiny_design()
    for head,width in [('volume',1),('shape',40),('quality',41)]:
        priors=annual_priors(d,head,[])
        rng=np.random.default_rng(4)
        beta=rng.normal(0,.01,(len(d.columns),width))
        gamma=np.zeros(8)
        flat=np.r_[beta.ravel(),gamma] if head=='volume' else beta.ravel()
        loss,grad=head_objective(flat,d,head,priors)
        logits=np.asarray(d.X_event@beta[:3])+d.context_event@beta[3:]
        if head=='volume':
            eta=math.log(3)+logits[:,0]
            likelihood=np.dot(d.exposure_hours,np.exp(eta))-eta.sum()
        elif head=='shape':
            eta=np.log(d.annual_offsets['pi'])+logits@d.basis.T
            lp=eta-logsumexp(eta,axis=1)[:,None]
            likelihood=-sum(d.origin_weights[k]*lp[e,d.origin_cells[k]] for e in range(2) for k in range(d.event_offsets[e],d.event_offsets[e+1]))
        else:
            eta=math.log(.15/.85)+logits[:,0,None]+logits[:,1:]@d.basis.T
            likelihood=-sum(d.origin_weights[k]*(d.neutral_goal_probability[k]*(-np.logaddexp(0,-eta[e,d.origin_cells[k]]))+(1-d.neutral_goal_probability[k])*(-np.logaddexp(0,eta[e,d.origin_cells[k]]))) for e in range(2) for k in range(d.event_offsets[e],d.event_offsets[e+1]))
        zero,_=head_objective(np.zeros_like(flat),d,head,priors)
        assert np.isfinite(loss) and np.isfinite(zero)
        # remove independently calculated diagonal normal penalties.
        precision=np.ones_like(beta)
        precision[0]=.25 if width==1 else (40. if head=='shape' else np.r_[.25,np.full(40,40.)])
        precision[1:3]=16 if width==1 else (640. if head=='shape' else np.r_[16.,np.full(40,640.)])
        precision[3]=1 if width==1 else (160. if head=='shape' else np.r_[1.,np.full(40,160.)])
        assert abs(loss-likelihood-.5*np.sum(precision*beta**2))<1e-10,(head,loss,likelihood)
        for i in rng.choice(len(flat),min(12,len(flat)),replace=False):
            step=np.zeros_like(flat);step[i]=1e-6
            fd=(head_objective(flat+step,d,head,priors)[0]-head_objective(flat-step,d,head,priors)[0])/2e-6
            assert abs(fd-grad[i])<2e-6,(head,i,fd,grad[i])
    c=np.exp(np.arange(16)[:,None]*np.array([[.13,.02]]))
    actual=spatial_shapley(c)
    independent=np.zeros((4,2))
    for order in permutations(range(4)):
        subset=0
        for group in order:
            updated=subset|(1<<group)
            independent[group]+=(c[updated]-c[subset])/24
            subset=updated
    assert np.allclose(actual,independent,atol=1e-14,rtol=0)
    print('independent objectives, gradients and 24-order accounting: green')

if __name__=='__main__': main()
