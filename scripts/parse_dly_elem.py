"""Parse GHCN-Daily .dly -> annual TMIN, TMAX, and composite TAVG per station (raw, no homogenization).
Monthly element mean needs >=20 valid QC-passing days; annual needs >=11 valid months.

This is the generator of data/annual_by_elem.csv (Data Records #1). Needs the
raw .dly archive, not redistributed with this release (see README:
"Regenerating the raw daily archive" for the NOAA AWS sync command). Point DLY
at wherever you synced it."""
import os, glob, numpy as np, pandas as pd
from pathlib import Path
def _data_dir():
    """Where the Zenodo release was unpacked: --data, else $UHI_AIR_DATA, else ../data."""
    import argparse as _ap, os as _os
    _p = _ap.ArgumentParser(add_help=False)
    _p.add_argument("--data", default=_os.environ.get(
        "UHI_AIR_DATA", str(Path(__file__).resolve().parent.parent / "data")))
    _d = Path(_p.parse_known_args()[0].data)
    if not _d.is_dir():
        raise SystemExit(
            f"data directory not found: {_d}\n"
            "Download the dataset from https://doi.org/10.5281/zenodo.22006933 and pass its\n"
            "location with --data /path/to/data (or set UHI_AIR_DATA).")
    return _d

DATA = _data_dir()
import argparse as _ap
_dp=_ap.ArgumentParser(add_help=False); _dp.add_argument("--dly", default="dly")
DLY = _dp.parse_known_args()[0].dly; MIN_DAYS = 20; MIN_MON = 11
def parse(path):
    mon = {}  # (yr,mo) -> {'TMAX':m,'TMIN':m,'TAVG':m}
    for ln in open(path, encoding="latin-1"):
        el = ln[17:21]
        if el not in ("TMAX", "TMIN", "TAVG"): continue
        yr = int(ln[11:15]); mo = int(ln[15:17]); vals = []
        for d in range(31):
            b = 21 + d*8; v = ln[b:b+5]
            if v == "-9999": continue
            if ln[b+6] != " ": continue
            try: vals.append(int(v)/10.0)
            except: pass
        if len(vals) >= MIN_DAYS: mon.setdefault((yr, mo), {})[el] = np.mean(vals)
    yr_el = {}  # yr -> {'TMIN':[..],'TMAX':[..],'TAVG_comb':[..]}
    for (yr, mo), e in mon.items():
        d = yr_el.setdefault(yr, {"TMIN": [], "TMAX": [], "TAVGc": []})
        if "TMIN" in e: d["TMIN"].append(e["TMIN"])
        if "TMAX" in e: d["TMAX"].append(e["TMAX"])
        if "TMAX" in e and "TMIN" in e: d["TAVGc"].append((e["TMAX"]+e["TMIN"])/2)
        elif "TAVG" in e: d["TAVGc"].append(e["TAVG"])
    out = {}
    for yr, d in yr_el.items():
        rec = {}
        for k, col in [("TMIN", "tmin"), ("TMAX", "tmax"), ("TAVGc", "tavg")]:
            rec[col] = float(np.mean(d[k])) if len(d[k]) >= MIN_MON else np.nan
        out[yr] = rec
    return out
# The raw GHCN-Daily .dly archive is not part of the Zenodo deposit: it is large and available
# unchanged from NOAA. Without it this script would parse zero files and write an empty table
# straight over a deposited output, so it stops here instead of failing silently.
_found = sorted(Path(DLY).glob("*.dly")) if Path(DLY).is_dir() else []
if not _found:
    raise SystemExit(
        f"no .dly files under {DLY!r}\n"
        "This step rebuilds the station panel from the raw GHCN-Daily archive, which is not\n"
        "redistributed here. Fetch it from NOAA (see the README) and point DLY at the unpacked\n"
        "directory, or set --dly /path/to/ghcnd_all.\n"
        "You do not need to re-run this to reproduce any result in the paper: its output,\n"
        "annual_by_elem.csv, is part of the deposit.")
files = glob.glob(f"{DLY}/*.dly"); print(f"parsing {len(files)} files (elementwise)...")
rows = []
for i, f in enumerate(files):
    sid = os.path.basename(f)[:-4]
    try: a = parse(f)
    except Exception: continue
    for yr, rec in a.items():
        rows.append((sid, yr, rec["tmin"], rec["tmax"], rec["tavg"]))
    if (i+1) % 1000 == 0: print(f"  {i+1}/{len(files)}")
df = pd.DataFrame(rows, columns=["id", "year", "tmin", "tmax", "tavg"])
df.to_csv(DATA/"annual_by_elem.csv", index=False)
print(f"stations: {df.id.nunique():,}  station-years: {len(df):,}")
print(f"years with TMIN: {df.tmin.notna().sum():,}  TMAX: {df.tmax.notna().sum():,}")
print("saved ghcnd/annual_by_elem.csv")
