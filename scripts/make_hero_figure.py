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
Output: figures/HERO_paper3.png  (Paper 2 house style: no in-figure title,
Okabe-Ito pairs, direct labelling in place of a legend)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import figstyle as fs

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
fs.use()

LAB = {"global": "all cities", "North America": "North America"}
x = np.arange(len(d))
w = 0.30

fig, ax = plt.subplots(figsize=(fs.W2 * 0.62, fs.W2 * 0.40))
ax.bar(x - 0.17, d.dUHI_raw_QCU, w, color=fs.BLUE, linewidth=0)
ax.bar(x + 0.17, d.dUHI_adjusted_QCF, w, color=fs.ORANGE, linewidth=0)

for xi, r in zip(x, d.itertuples()):
    # the loss reads as a fall from one level to the other, so carry it on a rule at the
    # raw level rather than an arrow across the panel
    drop = xi + 0.17 + w / 2 + 0.04          # clear of the bar so the value labels stay legible
    ax.plot([xi - 0.17 + w / 2, drop], [r.dUHI_raw_QCU] * 2,
            color=fs.GREY, lw=0.6, ls=(0, (2.5, 2)), zorder=1)
    ax.annotate("", xy=(drop, r.dUHI_adjusted_QCF),
                xytext=(drop, r.dUHI_raw_QCU),
                arrowprops=dict(arrowstyle="-|>", color=fs.GREY, lw=0.7,
                                shrinkA=0, shrinkB=0, mutation_scale=7))
    ax.plot([xi + 0.17 + w / 2, drop], [r.dUHI_adjusted_QCF] * 2,
            color=fs.GREY, lw=0.6, ls=(0, (2.5, 2)), zorder=1)
    ax.text(drop + 0.03, (r.dUHI_raw_QCU + r.dUHI_adjusted_QCF) / 2,
            f"\u2212{100 - r.retained_pct:.0f}%", color=fs.GREY, fontsize=7.5,
            ha="left", va="center", fontweight="bold")
    ax.text(xi - 0.17, r.dUHI_raw_QCU + 0.006, f"+{r.dUHI_raw_QCU:.2f}",
            color=fs.BLUE, fontsize=7.5, ha="center", va="bottom")
    ax.text(xi + 0.17, r.dUHI_adjusted_QCF + 0.006, f"+{r.dUHI_adjusted_QCF:.2f}",
            color=fs.ORANGE, fontsize=7.5, ha="center", va="bottom")
    ax.text(xi, -0.008, f"n = {r.n_raw} / {r.n_adj}", ha="center", va="top",
            fontsize=7, color=fs.GREY)

# direct labelling instead of a legend, as elsewhere in the series
fs.annotate(ax, 0.015, 0.99, "raw / unadjusted (QCU)", color=fs.BLUE)
fs.annotate(ax, 0.015, 0.90, "homogenized / adjusted (QCF)", color=fs.ORANGE)

ax.axhline(0, color=fs.INK, lw=0.6)
ax.set_xticks(x)
ax.set_xticklabels([LAB[p] for p in d.panel])
ax.set_ylabel("UHI intensification, 1971\u201390 to 2001\u201320 (\u00b0C)")
ax.set_ylim(-0.035, 0.265)
ax.set_xlim(-0.55, len(d) - 0.25)
ax.tick_params(axis="x", length=0)
for sp in ("top", "right", "bottom"):
    ax.spines[sp].set_visible(False)
ax.spines["left"].set_bounds(0, 0.25)      # the axis ends where the data does

_out = ROOT / "figures" / "HERO_paper3.png"
_out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(_out)
plt.close(fig)
print(f"HERO_paper3.png rebuilt from {len(d)} panels in house style")
print(d.to_string(index=False))
