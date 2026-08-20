"""Single-nearest vs multi-station representativeness: does one station per city adequately represent it?
(Technical Validation #6.) Reads only this release's own data/."""
import numpy as np, pandas as pd
from math import radians, cos
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
meta=pd.read_csv(DATA/"need_broad_meta.csv",dtype={"id":str}); S={r.id:(r.lat,r.lon,r.elev) for r in meta.itertuples()}
adf=pd.read_csv(DATA/"annual_by_elem.csv",dtype={"id":str}); TA={}
for r in adf.itertuples():
    if pd.notna(r.tavg): TA.setdefault(r.id,{})[r.year]=r.tavg
sids=[s for s in S if s in TA]; sarr=np.array([S[s][:2] for s in sids]); selev=np.array([S[s][2] for s in sids])
match=pd.read_csv(DATA/"city_station_match_broad.csv",dtype={"urban":str,"rural":str})
def m(sid):
    d=TA.get(sid,{}); x=[d[y] for y in range(2001,2021) if y in d]; return np.mean(x) if len(x)>=8 else np.nan
rows=[]; spreads=[]
for r in match.itertuples():
    d=np.hypot((sarr[:,0]-r.lat)*111,(sarr[:,1]-r.lon)*111*cos(radians(r.lat)))
    ui=[i for i in np.where(d<=25)[0] if not np.isnan(m(sids[i]))]
    rur=[x for x in (r.rural.split(";") if isinstance(r.rural,str) else []) if x in TA and not np.isnan(m(x))]
    if len(ui)<1 or len(rur)<3: continue
    rmed=np.median([m(x) for x in rur]); relev=np.nanmedian([S[x][2] for x in rur])
    uhis=[m(sids[i])-rmed+6.5/1000*(selev[i]-relev) for i in ui]
    nr=ui[int(np.argmin(d[ui]))]
    rows.append({"n_urb":len(ui),"uhi_single":m(sids[nr])-rmed+6.5/1000*(selev[nr]-relev),"uhi_multi":np.mean(uhis)})
    if len(uhis)>=2: spreads.append(np.std(uhis))
d=pd.DataFrame(rows)
print(f"cities {len(d)}; %≥2 urban stns {100*np.mean(d.n_urb>=2):.0f}%; nearest vs multi-mean corr {np.corrcoef(d.uhi_single,d.uhi_multi)[0,1]:.3f}, median|diff| {np.median(np.abs(d.uhi_single-d.uhi_multi)):.3f}")
print(f"within-city spread among urban stations: median SD {np.median(spreads):.2f} C")
