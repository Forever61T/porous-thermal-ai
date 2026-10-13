"""Run frozen No.1 protocols and generate figures, with no model selection."""
import argparse
import _bootstrap
from src.phase3.experiments import run
from src.phase3.figures import build_figures

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-reality-check', action='store_true')
    args = parser.parse_args()
    run(include_external=args.with_reality_check)
    build_figures(include_external=args.with_reality_check)
