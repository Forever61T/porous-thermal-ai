"""Public CPU replay: independently regenerate FVM data, fit, plot, test, verify.

No downloads or third-party data are needed for No.1. The optional reality check
requires a locally supplied, hash-verified Excel file; it is never redistributed.
Scientific model code, frozen parameters, splits and tolerances are unchanged.
"""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import _bootstrap
from src.common import ROOT, environment, save_json
from evaluate import compare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-no1', action='store_true', help='Reuse validated geometry/FVM cache.')
    parser.add_argument('--with-reality-check', action='store_true', help='Also audit locally supplied external Excel.')
    parser.add_argument('--with-ood', action='store_true', help='Also run the fixed light OOD diagnostic; no CNN.')
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = ROOT / 'results/reproduction' / stamp
    folder.mkdir(parents=True)
    for name in ['data/interim', 'data/processed', 'results/tables', 'reports']:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    record = dict(timestamp_utc=stamp, mode='public_no1_full_pipeline_replay',
                  environment=environment(), gpu_used=False, fresh_no1=not args.reuse_no1,
                  optional_external_reality_check=args.with_reality_check, steps=[])
    record['optional_ood_diagnostic']=args.with_ood
    try:
        if not args.reuse_no1:
            backup = ROOT / 'data/interim/reproduction_backups' / stamp
            backup.mkdir(parents=True)
            for name in ['data/interim/no1_images.npz', 'data/interim/no1_generation_manifest.json', 'data/processed/no1_samples.csv']:
                source = ROOT / name
                if source.exists():
                    shutil.move(str(source), str(backup / source.name))
        optional = ['--with-reality-check'] if args.with_reality_check else []
        commands = [(['scripts/audit_data.py'] + optional),
                    (['scripts/run_phase3.py'] + optional), ['-m', 'pytest', '-q']]
        if args.with_ood:
            commands.append(['scripts/run_ood.py'])
            commands.append(['scripts/build_ood_figures.py'])
        with (folder / 'console.log').open('w', encoding='utf-8') as log:
            for command in commands:
                step = time.perf_counter()
                print('Running:', ' '.join(command), flush=True)
                process = subprocess.Popen([sys.executable] + command, cwd=ROOT,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           text=True, encoding='utf-8', errors='replace')
                for line in process.stdout:
                    print(line, end='', flush=True)
                    log.write(line)
                code = process.wait()
                record['steps'].append(dict(command=command, exit_code=code, seconds=time.perf_counter()-step))
                if code:
                    raise RuntimeError('Pipeline stopped; inspect console.log. Do not change frozen references to force a pass.')
        record['comparison'] = compare()
        if args.with_ood:
            ood=json.loads((ROOT/'results/ood/run_manifest.json').read_text())
            assert ood['canonical_results_unchanged'] and ood['group_overlap']==0
            record['ood_manifest']=ood
            import pandas as pd
            import numpy as np
            expected=pd.read_csv(ROOT/'references/frozen_ood/metrics_summary.csv')
            actual=pd.read_csv(ROOT/'results/ood/metrics_summary.csv')
            keys=['protocol','model','method']
            expected=expected.sort_values(keys).reset_index(drop=True)
            actual=actual.sort_values(keys).reset_index(drop=True)
            assert expected[keys].equals(actual[keys])
            numeric=[c for c in expected if c not in keys]
            assert np.allclose(expected[numeric],actual[numeric],rtol=1e-9,atol=1e-9,equal_nan=True)
            ref=json.loads((ROOT/'references/frozen_ood/splits.json').read_text())
            generated=json.loads((ROOT/'results/ood/splits.json').read_text())
            assert ref==generated
            record['ood_comparison']=dict(summary_rows=len(actual),plans=len(generated['plans']),passed=True,
                max_numeric_difference=float(np.nanmax(np.abs(expected[numeric].to_numpy()-actual[numeric].to_numpy()))))
        record['status'] = 'FULL_REPRODUCTION_PASS'
    except Exception as error:
        record.update(status='FAILED', error=str(error))
        print('REPRODUCTION FAILED:', error, flush=True)
    finally:
        record['total_seconds'] = time.perf_counter()-started
        save_json(folder / 'machine_record.json', record)
        print(record['status'], flush=True)
        print('Evidence:', str((folder / 'machine_record.json').relative_to(ROOT)), flush=True)
    return 0 if record['status'] == 'FULL_REPRODUCTION_PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
