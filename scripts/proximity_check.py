"""Observational-site proximity check: does measured UHI depend on urban-station distance to centroid?
(Technical Validation #4.) Reads only this release's own data/."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf
from pathlib import Path
DATA = Path(__file__).resolve().parent.parent / "data"
uhi=pd.read_csv(DATA/"broad_groupings_cities.csv")[["city_id","uhi","uhi_tmin"]]
mt=pd.read_csv(DATA/"city_station_match_broad.csv")[["city_id","urban_km","n_rural"]]
d=uhi.merge(mt,on="city_id").dropna(subset=["uhi","urban_km"])
print(f"n={len(d)}; urban dist median {d.urban_km.median():.1f} km, 90th {d.urban_km.quantile(.9):.1f} km")
d["bin"]=pd.cut(d.urban_km,[0,5,10,15,25],labels=["0-5","5-10","10-15","15-25"])
for b in ["0-5","5-10","10-15","15-25"]:
    s=d[d.bin==b]; print(f"  {b:>6} km (n={len(s):>3}): mean {s.uhi.median():+.2f} | night {s.uhi_tmin.median():+.2f}")
for dv,l in [("uhi","mean"),("uhi_tmin","night")]:
    m=smf.ols(f"{dv} ~ urban_km",data=d.dropna(subset=[dv])).fit(cov_type="HC1")
    print(f"  {l} UHI ~ urban_km slope {m.params['urban_km']:+.4f} C/km (p={m.pvalues['urban_km']:.2f})")
for dv,l in [("uhi","mean"),("uhi_tmin","night")]:
    print(f"  {l}: all {d[dv].median():+.2f} | <10km {d[d.urban_km<10][dv].median():+.2f}")
