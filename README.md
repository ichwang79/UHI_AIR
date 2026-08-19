# UHI_AIR

Construction and validation scripts for a raw, homogenization-free global air-temperature urban heat-island (UHI) dataset built from GHCN-Daily (1941–2020).

The dataset these scripts build and validate is archived separately on Zenodo — DOI `10.5281/zenodo.XXXXXXX` (placeholder, update once minted), licensed **CC-BY-4.0**. This repository holds only the code, licensed **MIT**.

All scripts read exclusively from the deposited `data/` files (no absolute or machine-specific paths); each resolves its data directory relative to its own location via `Path(__file__).resolve().parent.parent / "data"`.

## Scripts

### Raw `.dly` parsing
Needs the raw GHCN-Daily archive, not redistributed with the dataset (see below).

| script | output |
|---|---|
| `parse_dly.py` | annual TAVG per station |
| `parse_dly_elem.py` | annual TMIN/TMAX/TAVG per station — generates `data/annual_by_elem.csv` |
| `parse_dly_seasonal.py` | per station-year JJA/DJF seasonal TAVG |

### Technical validation
Each reads only the deposited `data/` files.

| script | check |
|---|---|
| `multi_site.py` | single-station vs multi-station representativeness |
| `proximity_check.py` | does measured UHI depend on urban-station distance to city centroid? |
| `siting_and_divergence.py` → `refined_siting.py` → `sharpen_citysize.py` | three-step chain: airport/cooperative station-siting stratification and station–satellite divergence, refined via GHCN metadata, then isolated from a city-size confound |
| `make_hero_figure.py` | rebuilds the headline figure (raw vs. homogenized UHI intensification) from `data/homogenization_sensitivity.csv` |

## Regenerating the raw daily archive

Raw daily `.dly` files (~11 GB for the 8,666 stations this dataset uses) are deliberately not redistributed — they are large, unchanged NOAA public-domain files, available in full from the GHCN-Daily AWS Open Data bucket:

```bash
aws s3 sync s3://noaa-ghcn-pds/ghcnd_all/ ./dly --no-sign-request
```

That pulls the full ~132,501-station archive (~30 GB); the dataset's `need_broad_meta.csv` and `need_stations_meta.csv` give the exact station-ID lists actually needed, to filter down before or after syncing. Once `./dly` is populated, `parse_dly.py`, `parse_dly_elem.py`, and `parse_dly_seasonal.py` rebuild the annual, per-element, and seasonal panels from it.

## License

Code: MIT. Dataset (Zenodo): CC-BY-4.0.
