"""Generate and audit project-owned No.1 data; optional external data stays local."""
import argparse
import json
import _bootstrap
from src.common import ROOT, environment, save_json
from src.data.generate_no1 import generate_no1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-reality-check', action='store_true')
    args = parser.parse_args()
    for folder in ['data/interim', 'data/processed', 'results/tables']:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    save_json(ROOT / 'results/tables/environment.json', environment())
    if args.with_reality_check:
        from src.data.clean_data import audit_no2
        print(json.dumps(audit_no2(), indent=2))
    print(json.dumps(generate_no1(), indent=2))
