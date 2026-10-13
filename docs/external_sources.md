# External sources and implementation attribution

Checked 2026-10-14. Links below are references; no author repositories, downloaded
notebooks, paper PDFs, supporting information or external Excel records are
redistributed. Our `src/`, `scripts/`, features, geometry/FVM solver and experiments
are independent implementations created with Codex assistance.

| Source | Identifier / official link | What informed this project | What was not copied |
|---|---|---|---|
| Wei, Bao & Ruan, IJHMT 2020 | [10.1016/j.ijheatmasstransfer.2020.120176](https://doi.org/10.1016/j.ijheatmasstransfer.2020.120176) | morphology-aware thermal prediction | QSGS/FEM images/labels not obtained; Gaussian/FVM data here are new |
| Bruggeman 1935 | [10.1002/andp.19354160705](https://doi.org/10.1002/andp.19354160705) | effective-medium equation | no article figure or text reproduced |
| Lu et al., IJHMT 2022 | [10.1016/j.ijheatmasstransfer.2021.122305](https://doi.org/10.1016/j.ijheatmasstransfer.2021.122305) | shape-parameter extension motivation | no neural network code/data reused |
| MXene active learning | [paper](https://doi.org/10.1038/s41467-024-49011-8), [code](https://github.com/oshin71/Programmable-MXene-Aerogel), [data](https://zenodo.org/records/10779454) | separate original/candidate/augmented samples and explicit seeds | no MLP or active-learning code copied |
| Nanoporous heat capacity | [paper](https://doi.org/10.1038/s41563-022-01374-3), [code](https://github.com/SeyedMohamadMoosavi/tools-cp-porousmat) | group by parent structure, not site | no notebook/site data shipped; heat capacity is not conductivity |
| Silica experimental database | [paper](https://doi.org/10.1021/acs.chemmater.2c03459), [repository](https://github.com/jameskferri/Aerogel_ML_Neo4j), [SI](https://acs.figshare.com/articles/journal_contribution/23581981) | local-only conservative data audit | no author cleaning/training code or row-level data shipped |
| MAST-ML | [repository](https://github.com/uw-cmg/MAST-ML) | group-aware evaluation and domain awareness | no toolbox/source copied |
| OpenPNM | [repository](https://github.com/PMEAL/OpenPNM) | separate transport boundary conditions from surrogate fitting | our pixel FVM is not OpenPNM/pore-network code |
| TherML | [repository](https://github.com/hitarth64/TherML) | distinguish prior knowledge and empirical correction | its prior/ranking workflow is not our additive EMT residual |
| scikit-learn | [paper](https://www.jmlr.org/papers/v12/pedregosa11a.html), [documentation](https://scikit-learn.org/stable/) | maintained RF/Ridge and split APIs | dependency installed normally; no library vendoring |

## Optional experimental reality check

Official snapshot commit:
`dbe5489f69263e89112b60e5a0e29ba84a0c3f30`.

[Raw Excel at the immutable author commit](https://raw.githubusercontent.com/jameskferri/Aerogel_ML_Neo4j/dbe5489f69263e89112b60e5a0e29ba84a0c3f30/backends/raw_si_aerogels.xlsx).

Save the unchanged file locally as `data/raw/P16_Silica_Aerogel_raw.xlsx`.
Expected SHA256:
`c0bdd68dd694abe35cad2c04373b6d36c091041942be3f2398153453e2b58c8e`.
Run `python scripts/run_all.py --with-reality-check`. `src/data/load_data.py`
checks the hash; `clean_data.py` writes unit conversions, unparsed entries,
flags and membership to a cleaning log without overwriting raw data.

The author repository has no detected license. Public visibility alone does not
grant a redistribution license. Keep downloaded and processed external records
local. Author licenses and publisher conditions remain in force; this project
makes no blanket claim to redistribution rights.
