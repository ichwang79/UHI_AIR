"""Re-parse .dly -> per station-year JJA and DJF mean TAVG (for seasonal UHI). TAVG=(TMAX+TMIN)/2.

Needs the raw .dly archive, not redistributed with this release (see README:
"Regenerating the raw daily archive" for the NOAA AWS sync command). Point DLY
at wherever you synced it; this script does not otherwise read from data/."""
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
DLY = _dp.parse_known_args()[0].dly; MIN_DAYS=20
def parse(path):
    mon={}
    for ln in open(path,encoding="latin-1"):
        el=ln[17:21]
        if el not in ("TMAX","TMIN","TAVG"): continue
        yr=int(ln[11:15]); mo=int(ln[15:17]); vals=[]
        for d in range(31):
            b=21+d*8; v=ln[b:b+5]
            if v=="-9999": continue
            if ln[b+6]!=" ": continue
            try: vals.append(int(v)/10.0)
            except: pass
        if len(vals)>=MIN_DAYS: mon.setdefault((yr,mo),{})[el]=np.mean(vals)
    # monthly TAVG
    mt={}
    for (yr,mo),e in mon.items():
        if "TMAX" in e and "TMIN" in e: mt[(yr,mo)]=(e["TMAX"]+e["TMIN"])/2
        elif "TAVG" in e: mt[(yr,mo)]=e["TAVG"]
    out=[]
    for yr in set(y for y,_ in mt):
        jja=[mt[(yr,m)] for m in (6,7,8) if (yr,m) in mt]
        djf=[mt[(yr,12)] for m in [12] if (yr,12) in mt]+[mt[(yr,m)] for m in (1,2) if (yr,m) in mt]
        r={}
        if len(jja)==3: r["jja"]=np.mean(jja)
        if len(djf)==3: r["djf"]=np.mean(djf)
        if r: out.append((yr,r.get("jja",np.nan),r.get("djf",np.nan)))
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
files=glob.glob(f"{DLY}/*.dly"); print(f"parsing {len(files)} files (seasonal)...")
rows=[]
for i,f in enumerate(files):
    sid=os.path.basename(f)[:-4]
    try: o=parse(f)
    except: continue
    for yr,jja,djf in o: rows.append((sid,yr,jja,djf))
    if (i+1)%2000==0: print(f"  {i+1}/{len(files)}")
df=pd.DataFrame(rows,columns=["id","year","jja","djf"])
df.to_csv(DATA/"seasonal_tavg.csv",index=False)
print(f"stations {df.id.nunique()}, station-years {len(df)}; saved seasonal_tavg.csv")
