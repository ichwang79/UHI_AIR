#!/usr/bin/env python3
"""
verify_release.py — check that the analysis-ready layer follows from the raw layer.

Technical Validation section 9 offers reference values a correct rebuild must return.
This script recomputes them from the deposited files alone, so the check can be run
by anyone holding the release without any input from the analysis papers.

    UHI ~ log10(population), country-clustered SEs, on the full-record climatology

Run:
    python3 verify_release.py [--data ../data]

Exit status is 0 if every reference value matches within tolerance, 1 otherwise.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# Reference values, on the deposited route: longrecord_city_uhi.csv joined to the
# `pop` field of city_population.csv. Slopes are degrees C per tenfold population.
REFERENCE = {
    "uhi_tmax": ("daytime", -0.165, 667),
    "uhi_tavg": ("mean", +0.231, 903),
    "uhi_tmin": ("nocturnal", +0.656, 667),
}
TOL_SLOPE = 0.005
HERE = Path(__file__).resolve().parent


def size_law(d: pd.DataFrame, y: str):
    s = d.dropna(subset=[y, "lp", "country"])
    m = smf.ols(f"{y} ~ lp", data=s).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(s.country)[0]})
    return m.params["lp"], m.bse["lp"], m.pvalues["lp"], len(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE.parent / "data"),
                    help="directory holding the released CSVs")
    a = ap.parse_args()
    D = Path(a.data).expanduser().resolve()

    lvl = pd.read_csv(D / "longrecord_city_uhi.csv")
    pop = pd.read_csv(D / "city_population.csv")[["city_id", "pop"]]
    d = lvl.merge(pop, on="city_id", how="left")
    d = d[d["pop"] > 0].copy()
    d["lp"] = np.log10(d["pop"])

    print(f"  release: {D}")
    print(f"  {len(lvl)} cities in the climatology, {len(d)} with a positive population\n")
    print(f"  {'element':10s} {'slope':>8s} {'SE':>7s} {'p':>10s} {'n':>6s}   {'reference':>10s}  status")

    ok = True
    for col, (label, ref_slope, ref_n) in REFERENCE.items():
        b, se, p, n = size_law(d, col)
        good = abs(b - ref_slope) <= TOL_SLOPE and n == ref_n
        ok &= good
        print(f"  {label:10s} {b:+8.3f} {se:7.3f} {p:10.2g} {n:6d}   "
              f"{ref_slope:+10.3f}  {'OK' if good else 'MISMATCH'}")

    # The daytime column is the identity 2*tavg - tmin; confirm that holds, since a
    # user may reasonably expect it to be an independent measurement (Data Records #8).
    c = d.dropna(subset=["uhi_tmax", "uhi_tavg", "uhi_tmin"])
    resid = (c.uhi_tmax - (2 * c.uhi_tavg - c.uhi_tmin)).abs().max()
    print(f"\n  uhi_tmax == 2*uhi_tavg - uhi_tmin to {resid:.1e} over {len(c)} cities")

    print("\n  " + ("all reference values reproduce" if ok
                    else "REBUILD DOES NOT MATCH THE REFERENCE VALUES"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
