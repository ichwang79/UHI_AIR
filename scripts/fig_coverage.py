"""
Paper 3 Figure 1: what is in the record, and where.

The descriptor previously opened on the homogenization test — a justification for how the
record is built, not a view of the record itself. A reader deciding whether to reuse a
dataset wants to see its coverage and its distribution before its methodology, and the
paper's honesty about the developed-world concentration lands harder as a map than as a
sentence.

  a  every city in the 2000-2020 broad set, and which of them also carry a long record
     (>=1955 to >=2010) that supports the 1941-2020 analyses. The North American and
     European concentration the Usage Notes warn about is the thing you see first.

  b  the UHI distribution on both working sets, mean and nocturnal. This is where the
     record's most surprising property is visible: a large minority of cities read
     negative, and the share depends on which element and which working set is used —
     both facts a reuser has to know before computing anything.

Inputs, all released with the record: broad_city_uhi.csv, longrecord_city_uhi.csv,
city_station_match_broad.csv (coordinates).

Output: ../figures/Fig1_coverage.png
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

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


D = _data_dir()
OUT = Path(__file__).resolve().parent.parent / "figures" / "Fig1_coverage.png"
OUT.parent.mkdir(parents=True, exist_ok=True)
fs.use()

broad = pd.read_csv(D / "broad_city_uhi.csv")
longr = pd.read_csv(D / "longrecord_city_uhi.csv")
xy = pd.read_csv(D / "city_station_match_broad.csv")[["city_id", "lat", "lon"]].drop_duplicates("city_id")
b = broad.merge(xy, on="city_id", how="left")
b["longrecord"] = b.city_id.isin(set(longr.city_id))
print(f"broad {len(b):,} cities, of which {int(b.longrecord.sum()):,} long-record")

fig = plt.figure(figsize=(fs.W2, fs.W2 * 0.62))
gs = fig.add_gridspec(2, 1, height_ratios=[2.75, 1.0], hspace=0.28)
ax = fig.add_subplot(gs[0, 0])
axb = fig.add_subplot(gs[1, 0])

# --- a: coverage ---
# Natural Earth coastlines are a public asset, not part of the deposit. If they are not
# beside the script the map still draws — the cities carry the message, the land is backdrop.
_land = Path(__file__).resolve().parent / "assets" / "ne_110m_land.shp"
if _land.exists():
    import geopandas as gpd
    gpd.read_file(_land).plot(ax=ax, color="#EFEFEF", edgecolor="#D8D8D8", linewidth=0.25)
else:
    print("  note: assets/ne_110m_land.shp absent — drawing without the land backdrop\n"
          "        (get it from https://www.naturalearthdata.com, 1:110m physical, land)")
s = b[~b.longrecord]
ax.scatter(s.lon, s.lat, s=2.2, c=fs.GREY, alpha=0.75, linewidths=0, zorder=2,
           rasterized=True, label=f"2000–2020 only ({len(s):,})")
s = b[b.longrecord]
ax.scatter(s.lon, s.lat, s=2.6, c=fs.BLUE, linewidths=0, zorder=3,
           rasterized=True, label=f"also long-record, 1941–2020 ({len(s):,})")
ax.set_xlim(-180, 180); ax.set_ylim(-58, 84)
ax.set_axis_off(); ax.set_aspect("equal")
leg = ax.legend(loc="lower left", frameon=False, handletextpad=0.3,
                borderpad=0.1, labelspacing=0.35, markerscale=3.2)
share = b.continent.value_counts(normalize=True)
fs.annotate(ax, 0.02, 0.99, f"{len(b):,} cities", size=7.5)
fs.annotate(ax, 0.02, 0.925,
            f"Europe {100*share.get('Europe',0):.0f}%   "
            f"North America {100*share.get('North America',0):.0f}%   "
            f"Asia {100*share.get('Asia',0):.0f}%   rest {100*(1-share.get('Europe',0)-share.get('North America',0)-share.get('Asia',0)):.0f}%",
            color=fs.SLATE, size=7.0)
fs.panel_label(ax, "a", dx=0.0, dy=1.05)

# --- b: the UHI distribution on both sets ---
bins = np.arange(-3, 3.01, 0.15)
series = [(broad.uhi_tavg, "broad set, mean", fs.GREY),
          (broad.uhi_tmin, "broad set, night", fs.ORANGE),
          (longr.uhi_tavg, "long-record, mean", fs.PURPLE),
          (longr.uhi_tmin, "long-record, night", fs.BLUE)]
for v, lab, c in series:
    v = v.dropna()
    axb.hist(v, bins=bins, histtype="step", linewidth=1.1, color=c, density=True,
             label=f"{lab} \u2014 median {v.median():+.2f} °C, {100*(v<0).mean():.0f}% negative")
axb.axvline(0, color=fs.INK, lw=0.7, ls=(0, (3, 2)))
axb.set_xlabel("UHI intensity (°C)")
axb.set_ylabel("density")
axb.set_xlim(-3, 3)
axb.legend(loc="upper left", frameon=False, fontsize=7.0, labelspacing=0.32,
           handlelength=1.4, borderpad=0.2)
for sp in ("top", "right"):
    axb.spines[sp].set_visible(False)
axb.spines["left"].set_bounds(0, axb.get_ylim()[1])
fs.panel_label(axb, "b", dx=-0.055, dy=1.14)

fig.savefig(OUT)
for v, lab, _ in series:
    v = v.dropna()
    print(f"  {lab:22} n={len(v):5,}  median {v.median():+.2f}  negative {100*(v<0).mean():.1f}%")
print(f"Saved {OUT}")
