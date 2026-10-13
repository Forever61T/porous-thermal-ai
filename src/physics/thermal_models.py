"""Independent formulas and conservative FVM; no external repository code copied.

Inspired by Wei et al. IJHMT 2020 (10.1016/j.ijheatmasstransfer.2020.120176)
for morphology-aware benchmarking, and OpenPNM FourierConduction for separating
transport reference from ML. Our geometry, solver and boundaries differ.
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.optimize import minimize_scalar, least_squares

def bounds(phi, ks=100., kg=1.):
    phi=np.asarray(phi)
    return 1/((1-phi)/ks+phi/kg), (1-phi)*ks+phi*kg

def bruggeman(phi, ks=100., kg=1., a=1.):
    """Generalized self-consistent EMT; a=1 is 2D isotropic Bruggeman.

    sum_i f_i*(k_i-k)/(k_i+a*k)=0; positive quadratic root.
    a=(1-L)/L is an effective depolarization/shape parameter.
    """
    phi=np.asarray(phi);a=np.asarray(a)
    c=(1-phi)*(a*ks-kg)+phi*(a*kg-ks)
    disc=np.sqrt(c*c+4*a*ks*kg)
    # Stable evaluation of the positive root for negative c.
    return np.where(c>=0,(c+disc)/(2*a),2*ks*kg/(disc-c))

def fit_bruggeman(X,y,structure=False):
    phi=X['porosity'].to_numpy()
    if not structure:
        fit=minimize_scalar(lambda loga:np.mean((bruggeman(phi,a=np.exp(loga))-y)**2),
                            bounds=(np.log(.02),np.log(50)),method='bounded')
        return {'a':float(np.exp(fit.x))}
    z=np.column_stack([np.ones(len(X)),X['anisotropy'],X['bottleneck']-.5])
    fit=least_squares(lambda theta:bruggeman(phi,a=np.exp(np.clip(z@theta,-4,4)))-y,
                      x0=np.zeros(3),bounds=(-4,4),max_nfev=500)
    return {'theta':fit.x.tolist(),'fit_success':bool(fit.success)}

def predict_bruggeman(X,params):
    a=params.get('a',1.)
    if 'theta' in params:
        z=np.column_stack([np.ones(len(X)),X['anisotropy'],X['bottleneck']-.5])
        a=np.exp(np.clip(z@np.asarray(params['theta']),-4,4))
    return bruggeman(X['porosity'].to_numpy(),a=a)

def aerogel_scenario(X,params,cfg,observed_phi=False):
    """Conditional room-air hypothesis, NOT a verified experiment-specific model.

    k=A*(1-phi)^n + phi*k_air/(1+beta*lambda/d).
    Measurement T and p are absent. Radiation and solid-gas coupling neglected.
    """
    phi=X['phi_observed' if observed_phi else 'phi_density_scenario'].to_numpy()
    d=X['pore_nm'].to_numpy()
    A=params.get('A',cfg['raw_solid_coefficient_W_mK'])
    beta=params.get('beta',cfg['raw_knudsen_beta'])
    return A*(1-phi)**params.get('n',cfg['solid_exponent'])+phi*cfg['scenario_air_k_W_mK']/(1+beta*cfg['scenario_mean_free_path_nm']/d)

def fit_aerogel(X,y,cfg,observed_phi=False,fit_exponent=False):
    def params(z):
        p=dict(A=np.exp(z[0]),beta=np.exp(z[1]))
        if fit_exponent:p['n']=z[2]
        return p
    x0=list(np.log([.3,2.]));low=list(np.log([.001,.05]));high=list(np.log([20.,50.]))
    if fit_exponent:x0.append(2.);low.append(1.);high.append(3.)
    fit=least_squares(lambda z:aerogel_scenario(X,params(z),cfg,observed_phi)-y,
                      x0=x0,bounds=(low,high),max_nfev=500)
    return {**{k:float(v) for k,v in params(fit.x).items()},'fit_success':bool(fit.success)}

def solve_fvm(solid,ks=100.,kg=1.,return_field=False):
    """Cell-centered 2D div(k grad T)=0, left T=1/right T=0, top/bottom insulated.

    Square cells, harmonic face conductance, half-cell Dirichlet boundary.
    Q is integrated flux, keff=Q*L/W. No contact resistance, Knudsen or radiation.
    """
    k=np.where(np.asarray(solid,dtype=bool),ks,kg).astype(float)
    ny,nx=k.shape
    idx=np.arange(nx*ny).reshape(ny,nx)
    rr=[];cc=[];vv=[];diag=np.zeros(nx*ny)
    for left,right,kl,kr in [(idx[:,:-1],idx[:,1:],k[:,:-1],k[:,1:]),
                             (idx[:-1,:],idx[1:,:],k[:-1,:],k[1:,:])]:
        g=(2*kl*kr/(kl+kr)).ravel();i=left.ravel();j=right.ravel()
        np.add.at(diag,i,g);np.add.at(diag,j,g)
        rr.extend([i,j]);cc.extend([j,i]);vv.extend([-g,-g])
    bc_left=2*k[:,0];bc_right=2*k[:,-1]
    diag[idx[:,0]]+=bc_left;diag[idx[:,-1]]+=bc_right
    rhs=np.zeros(nx*ny);rhs[idx[:,0]]=bc_left
    rr.append(np.arange(nx*ny));cc.append(np.arange(nx*ny));vv.append(diag)
    A=coo_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(nx*ny,nx*ny)).tocsr()
    T=spsolve(A,rhs).reshape(ny,nx)
    qin=float(np.sum(bc_left*(1-T[:,0])));qout=float(np.sum(bc_right*T[:,-1]))
    result=dict(k_fvm=qin*nx/ny,flux_balance_relative=abs(qin-qout)/max(abs(qin),1e-15),
                linear_residual_relative=float(np.max(np.abs(A@T.ravel()-rhs))/max(np.max(rhs),1)))
    if return_field:result['temperature']=T
    return result
