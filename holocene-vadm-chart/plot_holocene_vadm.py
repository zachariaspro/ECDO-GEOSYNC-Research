#!/usr/bin/env python3
"""
Holocene Geomagnetic Dipole Moment — 18,000 Years of Earth's Magnetic Shield
============================================================================

Publication-quality plot of the Virtual Axial Dipole Moment (VADM) reconstruction
from the Late Glacial through present, with key paleomagnetic milestones marked.

Reconstruction draws on:
  - IGRF-14            (1900-2025 instrumental dipole)
  - gufm1              (1590-1990 historical observatory)
  - GEOMAGIA50         (Holocene archeomagnetic database)
  - CALS10k.2          (10-kyr spherical-harmonic Holocene model)
  - HOLOANTA           (Antarctic ice-core / sediment compilation)
  - GLOPIS-75          (Glacial-Holocene paleointensity stack)
  - BIGMUDIh.1         (Bayesian Holocene reconstruction)

Data is bundled as `holocene_vadm_data.csv` alongside this script. The CSV is a
curated synthesis matching the canonical features published in these references;
it is not a fit-derived product. To rebuild from primary sources, see references
at the bottom of this file.

Usage:
  python plot_holocene_vadm.py
Output:
  holocene_vadm_chart.png
  holocene_vadm_chart.pdf

License: MIT. Cite the original data sources, not this script, for science.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

# ----------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA = HERE / "holocene_vadm_data.csv"
OUT_PNG = HERE / "holocene_vadm_chart.png"
OUT_PDF = HERE / "holocene_vadm_chart.pdf"

# Publication style
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.titlesize": 17,
    "axes.titleweight": "bold",
    "axes.labelsize": 14,
    "axes.labelweight": "bold",
    "axes.linewidth": 1.0,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "xtick.major.width": 1.0,
    "ytick.major.width": 1.0,
    "legend.fontsize": 11,
    "legend.frameon": True,
    "legend.edgecolor": "#bbb",
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

# Colors (refined palette)
C_LINE       = "#1f4e79"
C_BAND       = "#9eb8d6"
C_TODAY      = "#c00000"
C_MAX        = "#d4a017"
C_MIN        = "#b03030"
C_DRYAS      = "#6b3a8c"
C_GRID       = "#dddddd"
C_THRESHOLD  = "#c00000"
C_TEXT       = "#222"

# ----------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------
df = pd.read_csv(DATA)
df = df.sort_values("age_BP", ascending=False).reset_index(drop=True)
age = df["age_BP"].values.astype(float)
vadm = df["vadm_1e22_Am2"].values.astype(float)
sigma = df["vadm_sigma_1e22_Am2"].values.astype(float)

PRESENT_VADM = 7.40    # IGRF-14 extrapolated through Jun 2026
HOLOCENE_MAX = 11.5
SEVEN_KA_MIN = 7.00
YD_MIN       = 4.5
THRESHOLD    = 7.00

# ----------------------------------------------------------------------
# Figure
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(15, 8.5))
ax.set_facecolor("#fafbfd")
fig.patch.set_facecolor("white")

# ----------------------------------------------------------------------
# Background era shading
# ----------------------------------------------------------------------
ax.axvspan(14700, 11700, color="#e0d4f2", alpha=0.45, zorder=0)
ax.text(13200, 12.55, "YOUNGER\nDRYAS",
        ha="center", va="center", fontsize=11, weight="bold",
        color="#6b3a8c", alpha=0.85, zorder=1)

ax.axvspan(9000, 6500, color="#fadbd8", alpha=0.50, zorder=0)
ax.text(7750, 12.55, "7 ka CRISIS",
        ha="center", va="center", fontsize=11, weight="bold",
        color="#b03030", alpha=0.85, zorder=1)

ax.axhspan(2, THRESHOLD, color="#fae9e7", alpha=0.45, zorder=0)

# ----------------------------------------------------------------------
# Uncertainty envelope
# ----------------------------------------------------------------------
ax.fill_between(age, vadm - sigma, vadm + sigma,
                color=C_BAND, alpha=0.55, linewidth=0, zorder=2)

# ----------------------------------------------------------------------
# Main VADM line
# ----------------------------------------------------------------------
ax.plot(age, vadm, "-", color=C_LINE, lw=2.0, zorder=3)
ax.scatter(age, vadm, s=10, color=C_LINE, zorder=4)

# ----------------------------------------------------------------------
# Threshold and Holocene-max reference lines
# ----------------------------------------------------------------------
ax.axhline(THRESHOLD, color=C_THRESHOLD, lw=2.2, alpha=0.85, zorder=2.5)
ax.axhline(HOLOCENE_MAX, color=C_MAX, ls="--", lw=1.0, alpha=0.55, zorder=2.5)
ax.axhline(PRESENT_VADM, color="#d97f30", ls=":", lw=1.2, alpha=0.7, zorder=2.5)

# ----------------------------------------------------------------------
# Milestone markers
# ----------------------------------------------------------------------
# Holocene maximum
ax.scatter([4500], [HOLOCENE_MAX], marker="s", s=180, color=C_MAX,
           edgecolors="black", linewidths=1.5, zorder=6)
ax.annotate(f"Holocene Maximum\n{HOLOCENE_MAX:.1f} × 10²² Am²",
            (4500, HOLOCENE_MAX), xytext=(5200, 12.85),
            fontsize=11, weight="bold", color="#9c7a0e",
            ha="center",
            arrowprops=dict(arrowstyle="-", color="#9c7a0e",
                             connectionstyle="arc3,rad=-0.25", lw=1.3))

# 7 ka minimum
ax.scatter([7000], [SEVEN_KA_MIN], marker="v", s=180, color=C_MIN,
           edgecolors="black", linewidths=1.5, zorder=6)
ax.annotate(f"7 ka Minimum\nBond Event 4",
            (7000, SEVEN_KA_MIN), xytext=(6200, 4.0),
            fontsize=11, weight="bold", color=C_MIN, ha="center",
            arrowprops=dict(arrowstyle="-", color=C_MIN,
                             connectionstyle="arc3,rad=0.25", lw=1.3))

# Younger Dryas / Gothenburg
ax.scatter([14600], [YD_MIN], marker="D", s=170, color=C_DRYAS,
           edgecolors="black", linewidths=1.5, zorder=6)
ax.annotate(f"Younger Dryas\nGothenburg Flip",
            (14600, YD_MIN), xytext=(14600, 2.7),
            fontsize=11, weight="bold", color=C_DRYAS, ha="center",
            arrowprops=dict(arrowstyle="-", color=C_DRYAS,
                             connectionstyle="arc3,rad=0.20", lw=1.3))

# Present marker (June 2026)
ax.scatter([-76], [PRESENT_VADM], marker="o", s=320, color=C_TODAY,
           edgecolors="black", linewidths=2.0, zorder=7)
ax.annotate(f"TODAY (Jun 2026)\n{PRESENT_VADM:.2f} × 10²² A·m²",
            (-76, PRESENT_VADM), xytext=(1400, 5.5),
            fontsize=11, weight="bold", color=C_TODAY, ha="center",
            arrowprops=dict(arrowstyle="-", color=C_TODAY,
                             connectionstyle="arc3,rad=0.30", lw=1.3))

# ----------------------------------------------------------------------
# Stats box (upper left)
# ----------------------------------------------------------------------
decline_pct = (HOLOCENE_MAX - PRESENT_VADM) / HOLOCENE_MAX * 100
margin_above_min = (PRESENT_VADM - SEVEN_KA_MIN) / SEVEN_KA_MIN * 100
stats = (
    f"Current field:     {PRESENT_VADM:.2f} × 10²² Am²\n"
    f"Decline from peak: {decline_pct:.0f}%\n"
    f"Margin above 7 ka low: {margin_above_min:.0f}%"
)
ax.text(0.012, 0.965, stats, transform=ax.transAxes,
        fontsize=11.5, weight="bold", color=C_TEXT,
        ha="left", va="top",
        bbox=dict(facecolor="white", edgecolor="#bbb",
                   boxstyle="round,pad=0.5", linewidth=1.0))

# ----------------------------------------------------------------------
# Axes — 18,000 BP on left, present on right
# ----------------------------------------------------------------------
ax.set_xlabel("Age (years BP, before 1950 CE)", labelpad=8)
ax.set_ylabel("Virtual Axial Dipole Moment  (×10²² Am²)", labelpad=8)
ax.set_title(
    "Holocene Geomagnetic Dipole Moment: 18,000 Years of Earth's Magnetic Shield",
    pad=14, color=C_TEXT)

# x-axis: BP convention reads largest-to-smallest left-to-right
ax.set_xlim(18500, -1500)
ax.set_ylim(2, 13.5)
ax.set_xticks(np.arange(0, 19000, 2000))
ax.set_yticks(np.arange(2, 14, 1))
ax.grid(True, which="major", color=C_GRID, lw=0.7, alpha=0.6, zorder=0)
ax.set_axisbelow(True)

# Legend
handles = [
    Line2D([0], [0], color=C_LINE, lw=2.5, label="VADM reconstruction"),
    patches.Patch(facecolor=C_BAND, alpha=0.55, label="Uncertainty (1σ)"),
    Line2D([0], [0], color=C_THRESHOLD, lw=2.2, label="7 ka threshold (7.0)"),
    Line2D([0], [0], marker="s", color=C_MAX, markersize=12, lw=0,
           markeredgecolor="black", label="Holocene Maximum"),
    Line2D([0], [0], marker="v", color=C_MIN, markersize=12, lw=0,
           markeredgecolor="black", label="7 ka Minimum"),
    Line2D([0], [0], marker="D", color=C_DRYAS, markersize=11, lw=0,
           markeredgecolor="black", label="Younger Dryas"),
    Line2D([0], [0], marker="o", color=C_TODAY, markersize=13, lw=0,
           markeredgecolor="black", label="Present (Jun 2026)"),
]
ax.legend(handles=handles, loc="upper right", framealpha=0.96,
          edgecolor="#bbb", ncol=1, fontsize=10.5)

# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------
fig.text(0.5, 0.012,
         "Data: IGRF-14, GEOMAGIA50, CALS10k.2, GLOPIS-75, HOLOANTA, BIGMUDIh.1, gufm1   |   Zacharias",
         ha="center", fontsize=10, color="#888", style="italic")

# ----------------------------------------------------------------------
# Save
# ----------------------------------------------------------------------
plt.tight_layout(rect=(0, 0.025, 1, 1))
plt.savefig(OUT_PNG, facecolor="white")
plt.savefig(OUT_PDF, facecolor="white")
print(f"Wrote {OUT_PNG}")
print(f"Wrote {OUT_PDF}")

# ----------------------------------------------------------------------
# Original data references (citation block for the GitHub README)
# ----------------------------------------------------------------------
"""
IGRF-14:    Alken P. et al. (2021/2025), International Geomagnetic Reference
            Field, Earth Planets Space.
gufm1:      Jackson A., Jonkers A.R.T., Walker M.R. (2000), Phil. Trans. R. Soc. A.
GEOMAGIA50: Brown M.C. et al. (2015), Earth Planets Space.
CALS10k.2:  Constable C., Korte M., Panovska S. (2016), Earth Planet. Sci. Lett.
HOLOANTA:   Lloyd S.J. et al. (2024), Earth Planet. Sci. Lett.
GLOPIS-75:  Laj C. et al. (2004), Phil. Trans. R. Soc. A.
BIGMUDIh.1: Arneitz P. et al. (2019), Geophys. J. Int.
"""
