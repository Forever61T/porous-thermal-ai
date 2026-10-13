# Open-source license and publication audit

Audit date: 2026-10-14. This is a file inclusion decision supported by source
notices, not a blanket legal opinion. Public history is newly initialized from an
allowlist; the private development repository/history is never pushed.

## Original material released

| Content | Source | License | Redistribution decision | GitHub treatment |
|---|---|---|---|---|
| `src/`, `scripts/`, `tests/`, configs, workflow | independently implemented for this project with Codex | MIT | released by maintainer | include |
| Synthetic 360 images/FVM labels and geometry recipe | this project; no author image dataset | CC BY 4.0 | project-owned | sample table/recipe included; image cache generated |
| No.1 result tables, split plans and generated figures | this project's fixed numerical experiments | CC BY 4.0 | project-owned | include |
| Final report, README and original docs | this project's explanation and analysis | CC BY 4.0 | original prose/figures | include; external quotes/figures not copied |
| Optional real-data processed rows and cleaning events | derived from unlicensed experimental compilation | upstream permission unresolved | not relicensed as original data | exclude; manual local-only optional step |
| Reality-check aggregate interpretation | original analysis of locally audited source | report license covers our prose only | does not grant rights over records | limited aggregate discussion; no raw scatter/table records |
| Libraries | pip-managed dependencies | respective upstream licenses | no vendoring or relicensing | version pins only |

## Third-party downloads and sources

| Content | Source | License | May redistribute? | GitHub treatment |
|---|---|---|---|---|
| `P01_MXene_Training_Testing.xlsx` | [official source](https://zenodo.org/records/10779454) | Record-specific license not verified: current Zenodo API timed out | Conditional only where stated license verified; otherwise not established | Excluded; link only |
| `P01_MXene_author_code.zip` | [official source](https://github.com/oshin71/Programmable-MXene-Aerogel) | BSD-3-Clause at root; individual file notices also apply | Conditional only where stated license verified; otherwise not established | Excluded; link only |
| `P01_MXene_Source_Data.xlsx` | [official source](https://www.nature.com/articles/s41467-024-49011-8) | Per-attachment redistribution grant not established in this audit | Not established; do not redistribute | Excluded; link only |
| `P02_Porous_Heat_Capacity_author_code_and_data.zip` | [official source](https://github.com/SeyedMohamadMoosavi/tools-cp-porousmat) | MIT at repository root; data-specific coverage not presumed | Code conditional under MIT; dataset not automatically relicensed | Excluded; link only |
| `P08_Membrane_Source_Data.xlsx` | [official source](https://www.nature.com/articles/s41467-023-40257-2) | Per-attachment redistribution grant not established in this audit | Not established; do not redistribute | Excluded; link only |
| `E01_Cellulose_Fig3_Structure.xlsx` | [official source](https://www.nature.com/articles/s41560-023-01226-7) | Per-attachment redistribution grant not established in this audit | Not established; do not redistribute | Excluded; link only |
| `E01_Cellulose_Fig5_Thermal.xlsx` | [official source](https://www.nature.com/articles/s41560-023-01226-7) | Per-attachment redistribution grant not established in this audit | Not established; do not redistribute | Excluded; link only |
| `E01_Cellulose_Supplementary_Data.xlsx` | [official source](https://www.nature.com/articles/s41560-023-01226-7) | Per-attachment redistribution grant not established in this audit | Not established; do not redistribute | Excluded; link only |
| `E02_PMSQ_Source_Data.xlsx` | [official source](https://www.nature.com/articles/s41467-025-63356-8) | Per-attachment redistribution grant not established in this audit | Not established; do not redistribute | Excluded; link only |
| `P16_Silica_Aerogel_raw.xlsx` | [official source](https://github.com/jameskferri/Aerogel_ML_Neo4j) | No detected repository license | Not established; do not redistribute | Excluded; link only |
| `P16_Silica_Aerogel_author_code_and_data.zip` | [official source](https://github.com/jameskferri/Aerogel_ML_Neo4j) | No detected repository license | Not established; do not redistribute | Excluded; link only |
| `P16_Silica_Aerogel_SI.pdf` | [official source](https://acs.figshare.com/articles/journal_contribution/Silica_Aerogel_Synthesis_Process_Property_Predictions_by_Machine_Learning/23581981) | CC BY-NC 4.0 (ACS Figshare record) | Conditional only where stated license verified; otherwise not established | Excluded; link only |
| `references/papers/wei2020.pdf` | [DOI](https://doi.org/10.1016/j.ijheatmasstransfer.2020.120176) | No redistribution permission established | Not established | Excluded; DOI only |
| `references/papers/shape_factor.pdf` | [DOI](https://doi.org/10.1016/j.ijheatmasstransfer.2021.122305) | No redistribution permission established | Not established | Excluded; DOI only |
| `hitarth64/TherML` downloaded README/LICENSE/key scripts | [official repository](https://github.com/hitarth64/TherML) | MIT at root | Conditional with original notices | Excluded; conceptual acknowledgement only |
| `uw-cmg/MAST-ML` downloaded README/LICENSE/key scripts | [official repository](https://github.com/uw-cmg/MAST-ML) | MIT at root | Conditional with original notices | Excluded; conceptual acknowledgement only |
| `PMEAL/OpenPNM` downloaded README/LICENSE/key scripts | [official repository](https://github.com/PMEAL/OpenPNM) | MIT at root | Conditional with original notices | Excluded; conceptual acknowledgement only |

Downloaded author notebooks, checkpoints, datasets and figures inherit their
original notices, not this repository's MIT license. Permissive code can often
be redistributed with conditions; we choose to link it because it is not part
of our implementation. “Excluded” does not mean every such file is prohibited.

The standalone ACS SI is CC BY-NC 4.0; this does not establish a license for the
separate Excel database. Source-data and SI attachment licenses are not inferred
from the paper's access status. The optional database has no detected license
([GitHub source](https://github.com/jameskferri/Aerogel_ML_Neo4j)); GitHub's
[license guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
explains the importance of an explicit grant.

## Privacy, large-file and Git-history gate

The publication gate scans every intended file (including PDF text/metadata and
Git commit identities) for absolute user paths, credential-like assignments,
GitHub/AWS/private-key patterns, external data/code directories, external Excel
and notebooks, caches/checkpoints and oversized unrelated files. It reports
filenames/counts rather than printing potential secret values.

Only original report/chart PDFs are allowed. Private machine console logs,
old packaging ZIPs, Windows evidence, author snapshots and the private `.git`
are excluded. Commit identity uses the public GitHub handle and GitHub noreply
email. See `docs/evidence/publication_scan.json` for the actual gate result.

Full code/model/split comparisons remain enabled. The public entry excludes
only the licensing-uncertain experimental branch by default; it does not change
the frozen No.1 predictions, tolerance or physics parameters.
