"""Filter-free amplitude estimates of recent pole excursions.

Paper 1 reports the 2024-2026 Chandler and annual amplitudes as ~3.5 and ~3.2
mas respectively, obtained from a Butterworth bandpass + Hilbert envelope. This
script offers three independent and complementary checks that do not depend on
that filter pipeline:

  Method A - Raw RMS (only a long rolling-mean baseline removed)
  Method B - Raw peak-to-peak pole position range
  Method C - Lomb-Scargle periodogram amplitude in the Chandler and annual bands

If the wobble has truly collapsed to a few mas, all three should agree with the
bandpass/Hilbert result. If the bandpass/Hilbert estimate is being depressed by
edge behaviour, the other methods will not show that depression.
"""
import os
import numpy as np
import pandas as pd
from scipy.signal import lombscargle

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


def main():
    df = load_finals(IERS_PATH)
    y = df["year"].values
    px = df["px"].values.astype(float)
    py = df["py"].values.astype(float)
    cx = np.polyfit(y, px, 1)
    cy = np.polyfit(y, py, 1)
    px -= cx[0] * y + cx[1]
    py -= cy[0] * y + cy[1]

    # Method A: rolling 4-yr mean as baseline (much longer than Chandler+annual,
    # so it should not distort sub-yr signals)
    long_w = 1500
    bx = pd.Series(px).rolling(long_w, min_periods=long_w // 2, center=True).mean().values
    by = pd.Series(py).rolling(long_w, min_periods=long_w // 2, center=True).mean().values
    px_hp = px - bx
    py_hp = py - by

    epochs = [(1975, 1977), (1985, 1987), (1990, 1992), (1995, 1997),
              (2000, 2002), (2005, 2007), (2010, 2012), (2013, 2015),
              (2015, 2017), (2018, 2020), (2020, 2022), (2022, 2024),
              (2024, df["year"].max() + 0.01)]

    print("Method A: RMS pole excursion in 2-yr blocks (no bandpass filter)")
    print(f"{'Period':<14}{'RMS px (mas)':<16}{'RMS py (mas)':<16}{'2D RMS (mas)':<16}")
    for lo, hi in epochs:
        mask = (y >= lo) & (y < hi)
        if mask.sum() < 200:
            continue
        rx = np.sqrt(np.nanmean(px_hp[mask] ** 2))
        ry = np.sqrt(np.nanmean(py_hp[mask] ** 2))
        print(f"{lo:4.0f}-{hi:4.0f}    {rx:10.1f}      {ry:10.1f}      "
              f"{np.hypot(rx, ry):10.1f}")

    print()
    print("Method B: peak-to-peak pole range in 2-yr blocks (no filter at all)")
    print(f"{'Period':<14}{'P2P px (mas)':<16}{'P2P py (mas)':<16}")
    for lo, hi in epochs:
        mask = (y >= lo) & (y < hi)
        if mask.sum() < 200:
            continue
        px_w = px_hp[mask]
        py_w = py_hp[mask]
        p2p_x = np.nanmax(px_w) - np.nanmin(px_w)
        p2p_y = np.nanmax(py_w) - np.nanmin(py_w)
        print(f"{lo:4.0f}-{hi:4.0f}    {p2p_x:10.1f}      {p2p_y:10.1f}")

    print()
    print("Method C: Lomb-Scargle peak amplitude in Chandler and annual bands")
    print("(4-yr window centered on each test year, no filtfilt, no Hilbert FFT)")
    print(f"{'Center':<10}{'Chandler (mas)':<22}{'Annual (mas)'}")
    periods_chand = np.linspace(410, 470, 30)
    periods_ann = np.linspace(345, 390, 30)
    ang_chand = 2 * np.pi / periods_chand
    ang_ann = 2 * np.pi / periods_ann
    for yc in [1980, 1990, 2000, 2010, 2015, 2018, 2020, 2022, 2024, 2025]:
        mask = (y >= yc - 2.0) & (y < yc + 2.0)
        if mask.sum() < 200:
            continue
        t = df["mjd"].values[mask]
        sx = px_hp[mask]
        sy = py_hp[mask]
        valid = ~np.isnan(sx) & ~np.isnan(sy)
        t = t[valid]
        sx = sx[valid]
        sy = sy[valid]
        if len(t) < 200:
            continue
        N = len(t)
        Pxc = lombscargle(t, sx, ang_chand, normalize=False)
        Pyc = lombscargle(t, sy, ang_chand, normalize=False)
        Pxa = lombscargle(t, sx, ang_ann, normalize=False)
        Pya = lombscargle(t, sy, ang_ann, normalize=False)
        A_c = np.sqrt(2 * (Pxc + Pyc).max() / N)
        A_a = np.sqrt(2 * (Pxa + Pya).max() / N)
        print(f"{yc:6}        {A_c:10.1f}              {A_a:10.1f}")


if __name__ == "__main__":
    main()
