"""Parse GHCN-Daily .dly -> annual TMIN, TMAX, and composite TAVG per station (raw, no homogenization).
Monthly element mean needs >=20 valid QC-passing days; annual needs >=11 valid months.

This is the generator of data/annual_by_elem.csv (Data Records #1). Needs the
raw .dly archive, not redistributed with this release (see README:
"Regenerating the raw daily archive" for the NOAA AWS sync command). Point DLY
at wherever you synced it."""
import os, glob, numpy as np, pandas as pd
from pathlib import Path
DATA = Path(__file__).resolve().parent.parent / "data"
DLY = "dly"; MIN_DAYS = 20; MIN_MON = 11
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
