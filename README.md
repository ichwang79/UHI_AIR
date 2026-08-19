# submission package

**Title.** *A raw, homogenization-free global dataset of air-temperature urban heat-island intensity from GHCN-Daily, 1941–2020*

**One line.** A quality-controlled but explicitly **non-homogenized** air-temperature UHI record — because breakpoint homogenization removes the gradual urban signal it is built to measure — released with the code and derived panels that reproduce the two companion analyses exactly.

## Contents

| file | what it is |
|---|---|
| `Paper3_data_descriptor_submission.docx` | **the manuscript to submit** (no separate SI; the data dictionary is in the main text) |
| `Paper3_data_descriptor.md` | Markdown source |
| `cover_letter.md` / `.docx` | cover letter |
| `figures/` | Figure 1 (`HERO_paper3.png`) — raw versus homogenized UHI intensification, global and North America; rebuilt by `scripts/make_hero_figure.py` from `data/homogenization_sensitivity.csv` |
| `data/` | **the release itself**, 24 CSVs + 1 raw metadata list (see Data Records in the manuscript) |
| `scripts/` | 9 Python scripts: raw `.dly` parsing, UHI construction, and the technical-validation checks reported in the manuscript (station siting, proximity, multi-station representativeness) and Fig. 1. Scripts used only for the companion attribution/scaling papers' own analyses are not included here; all 9 read only from this package's own `data/`, with no absolute paths or machine-specific references |

Manuscript length ~2,990 words. Submission formatting: Times New Roman 12 pt, double-spaced, US Letter with 1-inch margins, continuous line numbers, bordered tables with repeating headers.

## What the release contains

Station-level: `annual_by_elem.csv` (annual TMIN/TMAX/TAVG), `station_overview.csv`, `need_broad_meta.csv` / `need_stations_meta.csv`.

City-level UHI: `broad_city_uhi.csv` (2000–2020, 1,664 cities, six continents), `longrecord_city_uhi.csv` (full-record climatology, mean/nocturnal/daytime), `balanced_uhi_cities.csv` (fixed stations across four 20-year windows), `city_uhi_epoch_panel.csv` (1975–2020 epochs), `decomposition_cities.csv` and `decomposition_cities_1971_90.csv`.

Matching: `city_station_match_broad.csv` and `city_station_match_longrecord.csv` — **these select different stations for the same city** (they agree on the urban station for 77 % of shared cities), so the set matching the intended analysis window must be used.

Predictors and auxiliaries: `city_population.csv`, `city_covariates.csv`, `city_predictors_panel.csv`, `hist_predictors.csv`, `city_lst_panel.csv`, plus `paper3_ghcnm_qcu_validation.csv` for the independent raw-archive cross-check.

## Reproducibility

The release is self-contained with respect to the companion analyses. `Paper2_UrbanClimate/scripts/make_inputs.py` rebuilds that paper's six analysis inputs from these files alone; **15 of its 16 result tables regenerated identically at first attempt, and all 16 once the distributed GDP spline basis is used rather than regenerated**. The Paper 1 decomposition reproduces exactly at both baselines via `decompose_city_warming.py` (n = 379 / 29.7 % and n = 708 / 9.8 %).

Technical Validation §9 in the manuscript documents this, together with the two provenance traps it exposed: level analyses use the full-record UHI rather than the 2000–2020 broad file, and the `pop` field of `city_population.csv` rather than a fresh GHS-UCDB extraction (which differs ~18 % by boundary convention).

## Before submitting — one hard gate

**GDJ requires the dataset deposited in an accredited repository with a citable DOI *at submission*, not on acceptance.** The manuscript currently carries the placeholder `10.5281/zenodo.XXXXXXX` in two places (Data Records and Data Availability & Licence). Deposit `data/` to Zenodo under CC-BY-4.0; push `scripts/` to GitHub under MIT and link the repo to Zenodo's GitHub integration so a tagged release mints its own code DOI (data and code have different licences, so they should be two records, not one). Replace both placeholders once minted.

Also: fill the author block, and complete the truncated `et al.` author lists in the five references before removing the "citation details should be verified" note.

## Regenerating the raw daily archive

Raw daily `.dly` files (~11 GB for the 8,666 stations this release uses) are deliberately not redistributed here — they are large, unchanged NOAA public-domain files, available in full from the GHCN-Daily AWS Open Data bucket:

```bash
aws s3 sync s3://noaa-ghcn-pds/ghcnd_all/ ./dly --no-sign-request
```

That pulls the full ~132,501-station archive (~30 GB); `data/need_broad_meta.csv` and `data/need_stations_meta.csv` give the exact station-ID lists this release actually needs, to filter down before or after syncing. Once `./dly` is populated, `scripts/parse_dly.py`, `parse_dly_elem.py` and `parse_dly_seasonal.py` rebuild the annual, per-element and seasonal panels from it — see each script's docstring for its exact output.
