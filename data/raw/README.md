# External raw data stays local

No external raw file is required for the official No.1 pipeline. Its raw input is
the deterministic generation recipe in `configs/no1.json`.

Optional reality check: obtain `backends/raw_si_aerogels.xlsx` yourself from the
source in `docs/external_sources.md`, save an unchanged local copy as
`data/raw/P16_Silica_Aerogel_raw.xlsx`, and run `python scripts/run_all.py --with-reality-check`.
The loader checks SHA256. No external data is automatically downloaded or pushed.
