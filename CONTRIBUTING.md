# Contributing

This is a small course project with frozen scientific experiments. Please open an
issue describing a reproducibility bug, incorrect number, citation or leakage
concern. Include Python/package versions, the command and the relevant error.
Remove local paths and any credentials from logs before sharing.

Run `python scripts/run_all.py` and `python -m pytest -q` before proposing a fix.
Do not replace `references/frozen_phase3/` to make a failing comparison pass.
Changes to models, features or splits belong to a separately labelled experiment,
not the v1.0.0 results. External datasets should be linked rather than uploaded
unless their redistribution license is independently verified.
