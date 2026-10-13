"""Protect experimental independence and the interpolation/extrapolation claims."""
import numpy as np
import pandas as pd
import pytest
from src.common import ROOT,config
from src.phase3.experiments import make_plans,fit_core


@pytest.fixture(scope='module')
def data():
    path=ROOT/'data/processed/no1_samples.csv'
    if not path.exists():pytest.skip('Run audit_data.py first.')
    return pd.read_csv(path)


def test_mother_groups_and_nested_fractions(data):
    plans=make_plans(data,config('phase3')); frame=data.set_index('sample_id')
    for p in plans:
        assert not set(p['train_ids'])&set(p['test_ids'])
        tr=frame.loc[p['train_ids']];te=frame.loc[p['test_ids']]
        assert not set(tr.geometry_group)&set(te.geometry_group)
        assert tr.groupby('geometry_group').size().eq(2).all()
        assert te.groupby('geometry_group').size().eq(2).all()
    for seed in {p['seed'] for p in plans}:
        nested=sorted([p for p in plans if p['seed']==seed and p['protocol']=='grouped_in_distribution'],key=lambda p:p['fraction'])
        assert [p['n_train_groups'] for p in nested]==[36,72,108,144]
        for a,b in zip(nested,nested[1:]):
            assert set(a['train_ids'])<set(b['train_ids'])
            assert a['test_ids']==b['test_ids']


def test_region_claims(data):
    cfg=config('phase3');plans=make_plans(data,cfg);f=data.set_index('sample_id')
    for protocol in cfg['fixed_region_protocols']:
        region=[p for p in plans if p['protocol']==protocol]
        assert all(p['train_ids']==region[0]['train_ids'] and p['test_ids']==region[0]['test_ids'] for p in region)
        tr=f.loc[region[0]['train_ids']];te=f.loc[region[0]['test_ids']]
        if protocol=='middle_phi_interpolation':
            assert set(te.target_porosity)=={.6} and .6 not in set(tr.target_porosity)
            assert tr.porosity.min()<te.porosity.min()<tr.porosity.max()
        elif protocol=='high_phi_extrapolation':
            assert te.porosity.min()>tr.porosity.max()
        else:
            assert set(te.family)=={'anisotropic'} and 'anisotropic' not in set(tr.family)


def test_test_labels_do_not_change_predictions(data):
    cfg=config('phase3');p=make_plans(data,cfg)[0];f=data.set_index('sample_id')
    tr=f.loc[p['train_ids']];te=f.loc[p['test_ids']].copy()
    before,_,params_before,_,_=fit_core(tr,te,cfg,p['seed'])
    te['k_fvm']=np.arange(len(te))*10.+5.
    after,_,params_after,_,_=fit_core(tr,te,cfg,p['seed'])
    assert params_before==params_after
    for name in before:np.testing.assert_array_equal(before[name],after[name])
