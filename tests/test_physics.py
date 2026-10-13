"""Independent analytic limits verify the numerical reference, not ML scores."""
import numpy as np
import pytest
from src.physics.thermal_models import solve_fvm,bruggeman,bounds

@pytest.mark.parametrize('solid,k',[(False,1.),(True,100.)])
def test_homogeneous(solid,k):
    out=solve_fvm(np.full((20,20),solid))
    assert out['k_fvm']==pytest.approx(k,rel=1e-10)
    assert out['flux_balance_relative']<1e-10

def test_series_layers():
    s=np.zeros((20,20),dtype=bool);s[:,:10]=True
    assert solve_fvm(s)['k_fvm']==pytest.approx(1/(.5/100+.5),rel=1e-10)

def test_parallel_layers():
    s=np.zeros((20,20),dtype=bool);s[:10,:]=True
    assert solve_fvm(s)['k_fvm']==pytest.approx(50.5,rel=1e-10)

def test_emt_endpoints_and_bounds():
    phi=np.linspace(0,1,101);k=bruggeman(phi);low,high=bounds(phi)
    assert k[0]==pytest.approx(100.) and k[-1]==pytest.approx(1.)
    assert np.all(k>=low-1e-10) and np.all(k<=high+1e-10)
