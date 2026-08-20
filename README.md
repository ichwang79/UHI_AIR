# UHI_AIR

Construction and validation scripts for a raw, homogenization-free air-temperature urban
heat-island (UHI) dataset built from GHCN-Daily, 1941–2020, covering 1,664 cities and
concentrated in the developed world.

| | DOI | Licence |
|---|---|---|
| **Code** (this repository) | [10.5281/zenodo.22006819](https://doi.org/10.5281/zenodo.22006819) | MIT |
| **Dataset** the scripts build and validate | [10.5281/zenodo.22006933](https://doi.org/10.5281/zenodo.22006933) | CC-BY-4.0 |

The dataset is not in this repository. Download it from its own DOI and point the scripts at it.

## Running the scripts

Every script resolves its data directory in the same order:

1. `--data /path/to/data` on the command line
2. the `UHI_AIR_DATA` environment variable
3. `../data` relative to the script, for anyone working inside the authoring tree

So from a fresh clone, with the Zenodo download unpacked anywhere:

```bash
python scripts/verify_release.py --data ~/Downloads/uhi_air_data
```

No script contains an absolute or machine-specific path. Nothing writes into the data
directory except the `parse_dly*` scripts, which regenerate deposited files from the raw NOAA
archive and refuse to run when that archive is absent rather than writing an empty table over
a deposited one.

Requirements: Python 3.9+, `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`.
`fig_coverage.py` additionally uses `geopandas`, and draws without a land backdrop if the
optional Natural Earth shapefile in `scripts/assets/` is missing.

## Scripts

### Reproducibility check

| script | what it does |
|---|---|
| `verify_release.py` | Recomputes the reference values of the data descriptor's Technical Validation from the deposited files alone, and exits non-zero on any mismatch. Start here: it needs nothing but the dataset. |

### Technical validation

Each reads only the deposited files.

| script | check |
|---|---|
| `multi_site.py` | single-station versus multi-station representativeness |
| `proximity_check.py` | does measured UHI depend on the urban station's distance to the city centroid? |
| `siting_and_divergence.py` → `refined_siting.py` → `sharpen_citysize.py` | three-step chain: airport/cooperative station-siting stratification and station–satellite divergence, refined against GHCN metadata, then isolated from a city-size confound |

### Figures

| script | output |
|---|---|
| `fig_coverage.py` | coverage and completeness of the release — where the cities are, and the UHI distribution on both working sets |
| `make_hero_figure.py` | raw versus homogenized UHI intensification, from `homogenization_sensitivity.csv` |
| `figstyle.py` | shared plotting style; not run directly |

### Raw `.dly` parsing

These rebuild deposited files from the raw GHCN-Daily archive, which is **not** redistributed
with the dataset (see below). They are not needed to reproduce any published result — their
outputs are already in the deposit.

| script | output |
|---|---|
| `parse_dly.py` | annual TAVG per station |
| `parse_dly_elem.py` | annual TMIN/TMAX/TAVG per station — regenerates `annual_by_elem.csv` |
| `parse_dly_seasonal.py` | per station-year JJA/DJF seasonal TAVG |

## Regenerating the raw daily archive

The raw daily `.dly` files are deliberately not redistributed: they are large, unchanged NOAA
public-domain files, available in full from the GHCN-Daily AWS Open Data bucket.

```bash
aws s3 sync s3://noaa-ghcn-pds/ghcnd_all/ ./dly --no-sign-request
```

That pulls the full 132,501-station archive. The dataset's `need_broad_meta.csv` and
`need_stations_meta.csv` give the exact station-ID lists actually used (8,666 stations clear
the quality and completeness thresholds), so the archive can be filtered before or after
syncing. Once `./dly` is populated:

```bash
python scripts/parse_dly_elem.py --dly ./dly --data /path/to/data
```

## Licence

Code: MIT. Dataset: CC-BY-4.0, at its own DOI above.
