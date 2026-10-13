"""Compare all 49 metric rows and 70 split plans with immutable references."""
import json
import _bootstrap
import numpy as np
import pandas as pd
from src.common import ROOT, sha256


def compare():
    ref = ROOT / 'references/frozen_phase3'
    for name in ['no1', 'phase3']:
        current = json.loads((ROOT / f'configs/{name}.json').read_text())
        expected = json.loads((ref / f'{name}.json').read_text())
        if current != expected:
            raise ValueError(f'Frozen scientific config changed: {name}')
    expected = pd.read_csv(ref / 'metrics_summary.csv')
    actual = pd.read_csv(ROOT / 'results/phase3/tables/metrics_summary.csv')
    keys = ['protocol', 'fraction', 'model']
    if expected.duplicated(keys).any() or actual.duplicated(keys).any():
        raise ValueError('Duplicate metric rows')
    if set(map(tuple, expected[keys].to_numpy())) != set(map(tuple, actual[keys].to_numpy())):
        raise ValueError('Missing/different metric definitions')
    merged = expected.merge(actual, on=keys, suffixes=('_ref', '_actual'))
    errors = {}
    for column in [c for c in expected.columns if c not in keys]:
        e = merged[column + '_ref'].to_numpy()
        a = merged[column + '_actual'].to_numpy()
        if not np.allclose(a, e, atol=1e-6, rtol=1e-7, equal_nan=True):
            raise ValueError(f'Metric mismatch beyond rounding tolerance: {column}')
        errors[column] = float(np.nanmax(abs(a-e)))
    expected_splits = json.loads((ref / 'splits.json').read_text())['splits']
    actual_splits = json.loads((ROOT / 'results/phase3/tables/splits.json').read_text())['splits']
    if expected_splits != actual_splits:
        raise ValueError('Training/test IDs or seed/count definitions differ')
    return dict(status='PASS', n_metric_rows=len(expected), n_split_plans=len(expected_splits),
                tolerances=dict(absolute=1e-6, relative=1e-7),
                max_abs_metric_differences=errors,
                label_csv_sha256=sha256(ROOT / 'data/processed/no1_samples.csv'),
                geometry_npz_sha256=sha256(ROOT / 'data/interim/no1_images.npz'),
                metrics_sha256=sha256(ROOT / 'results/phase3/tables/metrics_summary.csv'))


if __name__ == '__main__':
    print(json.dumps(compare(), indent=2))
