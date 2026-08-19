"""(1) Siting stratification: do airport-sited urban stations under-read UHI?
   (2) Station-satellite divergence: why r~0.14, and does it improve for cleaner subsets?
(Technical Validation #3 and #5.)

First step of a three-script chain, all reading only this release's own data/:
  1. siting_and_divergence.py (this)  -> data/divergence_cities.csv
  2. refined_siting.py                -> data/refined_siting_cities.csv
  3. sharpen_citysize.py

Part (2) needs the station-observed and satellite-corrected UHI side by side at
the same city-epochs; that joined panel is not itself one of the release's
files, so it is built here from two that are: city_uhi_epoch_panel.csv
(station uhi_obs) and city_lst_panel.csv (satellite UHI_corrected, density,
Koppen), merged on CityID and year."""
import numpy as np, pandas as pd, re
from pathlib import Path
from scipy import stats
DATA = Path(__file__).resolve().parent.parent / "data"
# --- airport flag from station names ---
NAME={}; WMO={}
for ln in open(DATA/"ghcnd-stations.txt", encoding="latin-1"):
    NAME[ln[0:11]]=ln[41:71].strip(); WMO[ln[0:11]]=ln[80:85].strip()
AIRPAT=re.compile(r"AIRPORT|\bAP\b|\bINTL\b|\bAFB\b|\bNAS\b|AERODROME|\bRGNL\b|\bMUNI AP\b")
def is_airport(sid):
    return bool(AIRPAT.search(NAME.get(sid,"")))
# --- city UHI levels + urban station ---
grp=pd.read_csv(DATA/"broad_groupings_cities.csv")          # city_id, uhi, uhi_tmin, continent, koppen...
mt=pd.read_csv(DATA/"city_station_match_broad.csv",dtype={"urban":str})[["city_id","urban"]]
d=grp.merge(mt,on="city_id",how="left")
d["airport"]=d.urban.map(is_airport)
d["has_wmo"]=d.urban.map(lambda s: WMO.get(s,"")!="")
print("=== (1) SITING STRATIFICATION ===")
print(f"urban stations: {len(d)}, airport-named: {d.airport.sum()} ({100*d.airport.mean():.0f}%), WMO-id: {d.has_wmo.sum()} ({100*d.has_wmo.mean():.0f}%)")
def cmp(sub,lbl):
    a=sub[sub.airport].uhi.dropna(); n=sub[~sub.airport].uhi.dropna()
    if len(a)<5 or len(n)<5: print(f"  {lbl:16} (too few)"); return
    U,p=stats.mannwhitneyu(a,n)
    print(f"  {lbl:16} airport n={len(a):>3} med {a.median():+.2f} (%neg {100*np.mean(a<0):.0f}) | core n={len(n):>3} med {n.median():+.2f} (%neg {100*np.mean(n<0):.0f}) | diff {n.median()-a.median():+.2f} p={p:.1e}")
print(f"{'group':16} {'airport-sited':>28} | {'core-sited':>26} | contrast")
cmp(d,"ALL")
for c in ["North America","Europe","Asia"]:
    cmp(d[d.continent==c],c)
print("  (interpretation: positive 'diff' = airport stations read LOWER UHI, i.e. siting bias)")
# night
an=d[d.airport].uhi_tmin.dropna(); nn=d[~d.airport].uhi_tmin.dropna()
if len(an)>=5 and len(nn)>=5:
    print(f"  NIGHT(TMIN)       airport n={len(an)} med {an.median():+.2f} | core n={len(nn)} med {nn.median():+.2f} | diff {nn.median()-an.median():+.2f}")

print("\n=== (2) STATION-SATELLITE DIVERGENCE ===")
obs=pd.read_csv(DATA/"city_uhi_epoch_panel.csv")                      # CityID, year, uhi_obs
lst=pd.read_csv(DATA/"city_lst_panel.csv")[["CityID","year","UHI_corrected","ln_popdensity","koppen_main_group"]]
pan=obs.merge(lst, on=["CityID","year"], how="inner").rename(
    columns={"UHI_corrected":"UHI_corrected_global_pooled","koppen_main_group":"koppen_climate_group"})
cc=pan.dropna(subset=["uhi_obs","UHI_corrected_global_pooled"]).groupby("CityID").agg(
    stn=("uhi_obs","mean"), sat=("UHI_corrected_global_pooled","mean"),
    lnpop=("ln_popdensity","mean"), kop=("koppen_climate_group","first")).reset_index()
cc=cc.merge(mt,left_on="CityID",right_on="city_id",how="left"); cc["airport"]=cc.urban.map(is_airport)
cc=cc.merge(grp[["city_id","continent"]],on="city_id",how="left")
def rr(s,lbl):
    s=s.dropna(subset=["stn","sat"])
    if len(s)<15: print(f"  {lbl:22} n={len(s):>4}  (too few)"); return
    r=np.corrcoef(s.stn,s.sat)[0,1]; sl,ic,_,p,_=stats.linregress(s.sat,s.stn)
    print(f"  {lbl:22} n={len(s):>4}  r={r:+.2f}  slope={sl:+.2f}  (stn mean {s.stn.mean():+.2f} vs sat {s.sat.mean():+.2f})")
print(f"overall cities: {len(cc)}")
rr(cc,"ALL")
rr(cc[~cc.airport],"core-sited only")
rr(cc[cc.airport],"airport-sited only")
rr(cc[cc.lnpop>cc.lnpop.median()],"large cities (top½ dens)")
rr(cc[cc.lnpop<=cc.lnpop.median()],"small cities (bot½ dens)")
for c in ["North America","Europe","Asia"]: rr(cc[cc.continent==c],c)
for k in ["A","B","C","D"]: rr(cc[cc.kop==k],f"Koppen {k}")
# bias & agreement
s=cc.dropna(subset=["stn","sat"])
print(f"\nmean station UHI {s.stn.mean():+.2f} vs satellite {s.sat.mean():+.2f} (satellite reads {s.sat.mean()-s.stn.mean():+.2f} higher)")
print(f"both-positive agreement: {100*np.mean((s.stn>0)&(s.sat>0)):.0f}%; sign agreement: {100*np.mean(np.sign(s.stn)==np.sign(s.sat)):.0f}%")
cc.to_csv(DATA/"divergence_cities.csv",index=False)
