"""Re-parse .dly -> per station-year JJA and DJF mean TAVG (for seasonal UHI). TAVG=(TMAX+TMIN)/2.

Needs the raw .dly archive, not redistributed with this release (see README:
"Regenerating the raw daily archive" for the NOAA AWS sync command). Point DLY
at wherever you synced it; this script does not otherwise read from data/."""
import os, glob, numpy as np, pandas as pd
from pathlib import Path
DATA = Path(__file__).resolve().parent.parent / "data"
DLY="dly"; MIN_DAYS=20
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
