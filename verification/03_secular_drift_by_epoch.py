"""Linear secular pole drift fit by epoch, 1973-present.

Papers 1 & 2 cite a long-term secular pole drift of ~4 mas/yr toward ~80 deg W
(consistent with classical GIA), and Paper 2 builds a theoretical case for
present-day forcing toward 75 deg W. This script simply fits the IERS Finals
Daily series to a linear trend in (px, py) over user-selected epoch windows
and reports the magnitude and direction.

IERS convention: x-axis toward Greenwich (0 deg), y-axis toward 90 deg W. So a
fitted (dx/dt, dy/dt) trend with positive components points northwest of
Greenwich. The bearing is atan2(dy/dt, dx/dt); positive values are west of
Greenwich, negative values are east. We print an explicit E/W suffix to avoid
ambiguity (the previous version of this script printed e.g. "-30 W" which was
self-contradictory).

Adhikari & Ivins (2016, Sci. Adv.) reported a documented eastward shift in the
pole-drift direction around 2005 attributed to ice-mass loss and terrestrial
water storage redistribution. The output below allows direct visual comparison
with that finding.
"""
import numpy as np

from iers_finals import load_finals, bearing_label


def fit_drift(df, lo, hi):
    d = df[(df["year"] >= lo) & (df["year"] < hi)]
    if len(d) < 30:
        return None
    y = d["year"].values
    cx = np.polyfit(y, d["px_mas"].values, 1)
    cy = np.polyfit(y, d["py_mas"].values, 1)
    dx, dy = cx[0], cy[0]
    return np.hypot(dx, dy), np.degrees(np.arctan2(dy, dx)), dx, dy, len(d)


def main():
    df = load_finals(only_final=True)
    print(f"{'Period':<14}{'Rate (mas/yr)':<16}{'Bearing':<14}"
          f"{'dx':<10}{'dy':<10}{'N':<7}")
    for lo, hi in [(1973, 1990), (1990, 2000), (2000, 2005),
                   (2005, 2010), (2010, 2015), (2015, 2020),
                   (2020, df["year"].max() + 0.01),
                   (1973, df["year"].max() + 0.01)]:
        r = fit_drift(df, lo, hi)
        if r:
            mag, lon, dx, dy, n = r
            print(f"{lo:4.0f}-{hi:4.0f}    {mag:6.2f}        {bearing_label(lon)}   "
                  f"{dx:+6.2f}    {dy:+6.2f}    {n}")


if __name__ == "__main__":
    main()
