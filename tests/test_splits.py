"""Check published split plans for leakage and nested data-size experiments."""
import json
import pytest
from src.common import ROOT

def test_frozen_splits():
    path=ROOT/'results/tables/splits.json'
    if not path.exists():pytest.skip('Run audit/train to create a split plan first.')
    splits=json.loads(path.read_text())['splits']
    for s in splits:
        assert not set(s['train_ids'])&set(s['test_ids'])
        if s['protocol']!='random':assert s['n_overlapping_groups']==0
    keys={(s['dataset'],s['protocol'],s['seed']) for s in splits}
    for key in keys:
        group=sorted([s for s in splits if (s['dataset'],s['protocol'],s['seed'])==key],key=lambda x:x['fraction'])
        for a,b in zip(group,group[1:]):
            assert set(a['train_ids'])<=set(b['train_ids'])
            assert a['test_ids']==b['test_ids']
