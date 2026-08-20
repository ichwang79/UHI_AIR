"""Refined siting stratification using GHCN metadata (WMO id, network code, GSN/CRN flags).
Cleanest test: US WBAN/airport (USW) vs US cooperative/town (USC) — same country, differ only in station type.
Global proxy: synoptic (WMO id) vs cooperative (no WMO). (Technical Validation #3.)

Second step of a three-script chain, all reading only this release's own data/:
  1. siting_and_divergence.py  -> data/divergence_cities.csv
  2. refined_siting.py (this)  -> data/refined_siting_cities.csv
  3. sharpen_citysize.py"""
import numpy as np, pandas as pd, re
from pathlib import Path
from scipy import stats
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
META={}
for l in open(DATA/"ghcnd-stations.txt",encoding="latin-1"):
    sid=l[0:11]; META[sid]=dict(net=l[2], name=l[41:71].strip(), gsn=l[72:75].strip(),
                                hcncrn=l[76:79].strip(), wmo=l[80:85].strip())
AIR=re.compile(r"AIRPORT|\bAP\b|\bINTL\b|\bAFB\b|\bNAS\b|AERODROME|\bRGNL\b")
def cls(sid):
    m=META.get(sid)
    if not m: return "unknown"
    ref = m["gsn"]=="GSN" or m["hcncrn"]=="CRN"
    airportname = bool(AIR.search(m["name"]))
    synoptic = (m["wmo"]!="" or m["net"] in ("W","M")) and not ref
    coop = m["net"]=="C"
    if ref: return "reference"
    if synoptic or airportname: return "synoptic/airport"
    if coop: return "cooperative"
    return "local/other"
d=pd.read_csv(DATA/"broad_groupings_cities.csv")
mt=pd.read_csv(DATA/"city_station_match_broad.csv",dtype={"urban":str})[["city_id","urban"]]
d=d.merge(mt,on="city_id"); d["cls"]=d.urban.map(cls); d["net"]=d.urban.map(lambda s:META.get(s,{}).get("net"))
d["country"]=pd.read_csv(DATA/"city_station_match_broad.csv").set_index("city_id").loc[d.city_id,"country"].values
print("=== urban-station classification (n=%d) ==="%len(d))
print(d.cls.value_counts().to_string())

def mw(a,b,la,lb):
    a=a.dropna(); b=b.dropna()
    if len(a)<5 or len(b)<5: print(f"  {la} vs {lb}: too few ({len(a)},{len(b)})"); return
    p=stats.mannwhitneyu(a,b)[1]
    print(f"  {la:22} n={len(a):>3} med {a.median():+.2f} (%neg {100*np.mean(a<0):.0f}) | {lb:16} n={len(b):>3} med {b.median():+.2f} (%neg {100*np.mean(b<0):.0f}) | diff {a.median()-b.median():+.2f} p={p:.1e}")

print("\n=== CLEAN TEST: US airport (USW) vs US cooperative (USC) — TAVG ===")
us=d[d.country=="USA"]
mw(us[us.net=="W"].uhi, us[us.net=="C"].uhi, "US airport (USW)", "US coop (USC)")
print("=== same, NIGHT (TMIN) ===")
mw(us[us.net=="W"].uhi_tmin, us[us.net=="C"].uhi_tmin, "US airport (USW)", "US coop (USC)")

print("\n=== GLOBAL: synoptic/airport vs cooperative vs local ===")
mw(d[d.cls=="synoptic/airport"].uhi, d[d.cls=="cooperative"].uhi, "synoptic/airport", "cooperative")
mw(d[d.cls=="synoptic/airport"].uhi, d[d.cls=="local/other"].uhi, "synoptic/airport", "local/other")

print("\n=== within-continent (NA) synoptic vs coop+local ===")
na=d[d.continent=="North America"]
mw(na[na.cls=="synoptic/airport"].uhi, na[na.cls.isin(["cooperative","local/other"])].uhi, "NA synoptic/airport", "NA coop/local")

# divergence r by refined class
print("\n=== DIVERGENCE r by refined siting class ===")
cc=pd.read_csv(DATA/"divergence_cities.csv"); cc["cls"]=cc.urban.map(cls)
for c in ["synoptic/airport","cooperative","local/other","reference"]:
    s=cc[cc.cls==c].dropna(subset=["stn","sat"])
    if len(s)>=15: print(f"  {c:18} n={len(s):>4}  r={np.corrcoef(s.stn,s.sat)[0,1]:+.2f}  (stn {s.stn.mean():+.2f} vs sat {s.sat.mean():+.2f})")
d.to_csv(DATA/"refined_siting_cities.csv",index=False)
