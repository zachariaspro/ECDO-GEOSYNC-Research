"""Linear secular pole drift fit by epoch, 1973-present.

Papers 1 & 2 cite a long-term secular pole drift of ~4 mas/yr toward ~80°W
(consistent with classical GIA), and Paper 2 builds a theoretical case for
present-day forcing toward 75°W. This script simply fits the IERS Finals Daily
series to a linear trend in (px, py) over user-selected epoch windows and
reports the magnitude and direction.

IERS convention: x-axis toward Greenwich (0°), y-axis toward 90°W. So a fitted
(dx/dt, dy/dt) trend corresponds to a great-circle bearing measured west of
Greenwich = atan2(dy/dt, dx/dt).

Adhikari & Ivins (2016, Sci. Adv.) reported a documented eastward shift in the
pole-drift direction around 2005 attributed to ice-mass loss and terrestrial
water storage redistribution. The output below allows direct visual comparison
with that finding.
"""
import os
import numpy as np
import pandas as pd

IERS_PATH = os.environ.get("IERS_PATH", "finals.all.iau2000.txt")


def load_finals(path):
    rows = []
    with open(path) as f:
        for ln in f:
            if len(ln) < 60:
                continue
            try:
                mjd = float(ln[7:15])
                flag = ln[16]
                px_s = ln[18:27].strip()
                py_s = ln[37:46].strip()
                if not px_s or not py_s:
                    continue
                rows.append((mjd, float(px_s) * 1000, float(py_s) * 1000, flag))
            except ValueError:
                continue
    df = pd.DataFrame(rows, columns=["mjd", "px", "py", "flag"])
    df["year"] = 2000.0 + (df["mjd"] - 51544.5) / 365.25
    return df[df["flag"] == "I"].sort_values("mjd").reset_index(drop=True)


def fit_drift(df, lo, hi):
    d = df[(df["year"] >= lo) & (df["year"] < hi)]
    if len(d) < 30:
        return None
    y = d["year"].values
    cx = np.polyfit(y, d["px"].values, 1)
    cy = np.polyfit(y, d["py"].values, 1)
    dx, dy = cx[0], cy[0]
    return np.hypot(dx, dy), np.degrees(np.arctan2(dy, dx)), dx, dy, len(d)


def main():
    df = load_finals(IERS_PATH)
    print(f"{'Period':<14}{'Rate (mas/yr)':<16}{'Direction (deg W)':<20}"
          f"{'dx':<10}{'dy':<10}{'N':<7}")
    for lo, hi in [(1973, 1990), (1990, 2000), (2000, 2005),
                   (2005, 2010), (2010, 2015), (2015, 2020),
                   (2020, df["year"].max() + 0.01), (1973, df["year"].max() + 0.01)]:
        r = fit_drift(df, lo, hi)
        if r:
            mag, lon, dx, dy, n = r
            print(f"{lo:4.0f}-{hi:4.0f}    {mag:6.2f}        {lon:8.2f}             "
                  f"{dx:+6.2f}    {dy:+6.2f}    {n}")


if __name__ == "__main__":
    main()
