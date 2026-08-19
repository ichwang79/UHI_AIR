"""Parse GHCN-Daily .dly files -> annual TAVG per station (UHI-preserving, no homogenization).
Monthly TAVG = (monthly-mean TMAX + monthly-mean TMIN)/2 when both present, else direct TAVG.
Only QC-passing daily values (Q_FLAG blank). Monthly mean needs >=20 valid days; annual needs >=11 months.

Needs the raw .dly archive, not redistributed with this release (see README:
"Regenerating the raw daily archive" for the NOAA AWS sync command). Point DLY
at wherever you synced it; this script does not otherwise read from data/."""
import os, glob, numpy as np, pandas as pd
from pathlib import Path
DATA = Path(__file__).resolve().parent.parent / "data"
DLY = "dly"   # path to the synced raw archive, relative to the current working directory
MIN_DAYS = 20      # valid days per month
MIN_MON  = 11      # valid months per year
def parse(path):
    # returns dict year -> annual tavg
    # accumulate monthly means per element
    mon = {}   # (year,month) -> {'TMAX':mean,'TMIN':mean,'TAVG':mean}
    for ln in open(path, encoding="latin-1"):
        el = ln[17:21]
        if el not in ("TMAX", "TMIN", "TAVG"): continue
        yr = int(ln[11:15]); mo = int(ln[15:17])
        vals = []
        for d in range(31):
            b = 21 + d*8
            v = ln[b:b+5]
            if v == "-9999": continue
            q = ln[b+6]
            if q != " ": continue          # failed QC flag
            try: vals.append(int(v)/10.0)   # tenths degC
            except: pass
        if len(vals) >= MIN_DAYS:
            mon.setdefault((yr, mo), {})[el] = np.mean(vals)
    ann = {}
    by_year = {}
    for (yr, mo), e in mon.items():
        if "TMAX" in e and "TMIN" in e: t = (e["TMAX"] + e["TMIN"])/2
        elif "TAVG" in e: t = e["TAVG"]
        else: continue
        by_year.setdefault(yr, []).append(t)
    for yr, ms in by_year.items():
        if len(ms) >= MIN_MON:
            ann[yr] = float(np.mean(ms))
    return ann

files = glob.glob(f"{DLY}/*.dly")
print(f"parsing {len(files)} .dly files...")
rows = []
for i, f in enumerate(files):
    sid = os.path.basename(f)[:-4]
    try: ann = parse(f)
    except Exception as ex: continue
    for yr, t in ann.items():
        rows.append((sid, yr, round(t, 3)))
    if (i+1) % 500 == 0: print(f"  {i+1}/{len(files)}")
df = pd.DataFrame(rows, columns=["id", "year", "tavg"])
df.to_csv(DATA/"annual_tavg.csv", index=False)
print(f"stations parsed: {df.id.nunique():,}  station-years: {len(df):,}")
print(f"year range: {df.year.min()}-{df.year.max()}")
print("saved ghcnd/annual_tavg.csv")
