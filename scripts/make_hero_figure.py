#!/usr/bin/env python3
"""
Rebuild HERO_paper3.png — the dataset's central validation figure — from the
deposited homogenization_sensitivity.csv.

That table compares each city's UHI intensification (1971-90 baseline to
2001-20) computed on the raw/unadjusted GHCN-M v4 monthly record (QCU) against
the same comparison on the homogenized/adjusted version of the same network
(QCF). It is deposited here rather than regenerated on the fly because building
it requires the raw GHCN-M v4 QCU and QCF station archives, which -- like the
GHCN-Daily .dly files -- are large NOAA/NCEI inputs not redistributed with this
release; only the derived per-panel medians are shipped.

Two panels only: global and North America. An earlier draft of this figure
carried Europe and Asia bars and a different (1941-60) baseline, but no
reproducible computation for those additional bars or that baseline could be
located, so this rebuild is restricted to what the deposited table actually
supports.

Input : data/homogenization_sensitivity.csv
Output: figures/HERO_paper3.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
ROOT = Path(__file__).resolve().parent.parent
d = pd.read_csv(DATA / "homogenization_sensitivity.csv")

BLUE, RED, GREY = "#1f6fb4", "#c0392b", "#666666"
labels = ["ALL" if p == "global" else p for p in d.panel]

fig, ax = plt.subplots(figsize=(9.5, 5.6))
x = np.arange(len(d))
ax.bar(x - 0.19, d.dUHI_raw_QCU, 0.36, color=BLUE, edgecolor="black", linewidth=0.4,
       label="raw / unadjusted (QCU)")
ax.bar(x + 0.19, d.dUHI_adjusted_QCF, 0.36, color=RED, edgecolor="black", linewidth=0.4,
       label="homogenized / adjusted (QCF)")

for xi, r in zip(x, d.itertuples()):
    cut = 100 - r.retained_pct
    ytop = max(r.dUHI_raw_QCU, r.dUHI_adjusted_QCF)
    ax.annotate(f"−{cut:.0f}%", xy=(xi - 0.19, r.dUHI_raw_QCU), xytext=(xi + 0.19, r.dUHI_adjusted_QCF),
                arrowprops=dict(arrowstyle="->", color=GREY, lw=1.1), fontsize=11,
                fontweight="bold", color=GREY, ha="center",
                va="bottom" if r.dUHI_adjusted_QCF >= 0 else "top")
    ax.text(xi, -0.014, f"n={r.n_raw}/{r.n_adj}", ha="center", va="top", fontsize=9, color=GREY)

ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel("UHI intensification, 1971–90 → 2001–20 (°C)", fontsize=10.5)
ax.legend(frameon=False, loc="upper right", fontsize=9.5)
na = d[d.panel == "North America"].iloc[0]
gl = d[d.panel == "global"].iloc[0]
fig.suptitle("Homogenization removes most of the urban heat-island signal\n"
             f"North America's +{na.dUHI_raw_QCU:.2f} °C intensification falls to "
             f"+{na.dUHI_adjusted_QCF:.2f} °C; the global signal falls by "
             f"{100 - gl.retained_pct:.0f}%",
             fontsize=13.5, fontweight="bold", y=0.98)
ax.set_ylim(-0.02, 0.24)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)

fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.subplots_adjust(top=0.80)
_out = ROOT / "figures" / "HERO_paper3.png"
_out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(_out, dpi=160)
plt.close(fig)
print(f"HERO_paper3.png rebuilt from {len(d)} panels")
print(d.to_string(index=False))
