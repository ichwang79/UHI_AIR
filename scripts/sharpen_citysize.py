"""Isolate SITING from CITY-SIZE in the US airport(USW) vs cooperative(USC) UHI difference.
(a) OLS: uhi ~ airport + ln(pop);  (b) stratify by population tercile;  (c) population-matched pairs.
(Technical Validation #3.) Third step of the siting-validation chain; see siting_and_divergence.py.

City population here is the raw GHSL 2020 total (`ghsl_population_2020.csv`), not the `pop`
field of city_population.csv -- the two differ systematically by boundary convention
(Data Records #10), and this check is about isolating a *within-network* size confound,
for which the raw GHSL total is the right, undistorted quantity."""
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
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
gh=pd.read_csv(DATA/"ghsl_population_2020.csv").rename(columns={"pop_2020_ghsl":"pop"})
d=pd.read_csv(DATA/"refined_siting_cities.csv").merge(gh,on="city_id",how="left")
us=d[(d.country=="USA")&(d.net.isin(["W","C"]))].dropna(subset=["pop"]).copy()
us["airport"]=(us.net=="W").astype(int); us["lnpop"]=np.log(us["pop"].clip(lower=1))
print(f"US clean sample: {len(us)} cities ({us.airport.sum()} airport/USW, {(1-us.airport).sum():.0f} coop/USC)")
print(f"median pop — airport {us[us.airport==1]["pop"].median():,.0f} vs coop {us[us.airport==0]["pop"].median():,.0f}  (size confound: {us[us.airport==1]["pop"].median()/us[us.airport==0]["pop"].median():.1f}x)")

print("\n=== (a) OLS: does airport survive controlling for ln(pop)? ===")
for dv in ["uhi","uhi_tmin"]:
    s=us.dropna(subset=[dv])
    m0=smf.ols(f"{dv} ~ airport",data=s).fit()
    m1=smf.ols(f"{dv} ~ airport + lnpop",data=s).fit()
    print(f"  {dv:9}: raw airport {m0.params['airport']:+.2f} (p{m0.pvalues['airport']:.0e}) | +ln(pop) airport {m1.params['airport']:+.2f} (p{m1.pvalues['airport']:.0e}), lnpop {m1.params['lnpop']:+.2f} (p{m1.pvalues['lnpop']:.0e})")

print("\n=== (b) stratify by population tercile (airport vs coop within each) ===")
us["ptile"]=pd.qcut(us.lnpop,3,labels=["small","mid","large"])
for t in ["small","mid","large"]:
    s=us[us.ptile==t]; a=s[s.airport==1].uhi.dropna(); c=s[s.airport==0].uhi.dropna()
    if len(a)>=5 and len(c)>=5:
        p=stats.mannwhitneyu(a,c)[1]
        print(f"  {t:6} pop: airport n={len(a):>3} med {a.median():+.2f} | coop n={len(c):>3} med {c.median():+.2f} | diff {a.median()-c.median():+.2f} p={p:.2f}")
    else: print(f"  {t:6} pop: airport n={len(a)}, coop n={len(c)} (too few)")

print("\n=== (c) population-matched pairs (each USW → nearest USC in ln pop, |Δln pop|<0.5) ===")
A=us[us.airport==1].dropna(subset=["uhi"]); C=us[us.airport==0].dropna(subset=["uhi"]).copy()
diffs=[]; used=set()
for _,a in A.iterrows():
    cand=C[(~C.city_id.isin(used))]
    if len(cand)==0: break
    j=(cand.lnpop-a.lnpop).abs().idxmin()
    if abs(C.loc[j,"lnpop"]-a.lnpop)<0.5:
        diffs.append(a.uhi-C.loc[j,"uhi"]); used.add(C.loc[j,"city_id"])
diffs=np.array(diffs)
if len(diffs)>=10:
    t,p=stats.wilcoxon(diffs)
    print(f"  {len(diffs)} matched pairs (Δln pop<0.5): mean airport−coop UHI = {diffs.mean():+.2f} °C, median {np.median(diffs):+.2f}, Wilcoxon p={p:.3f}")
    print(f"  → {'siting effect survives size-matching' if p<0.05 and np.median(diffs)>0 else 'effect attenuates after matching (was largely city size)'}")
