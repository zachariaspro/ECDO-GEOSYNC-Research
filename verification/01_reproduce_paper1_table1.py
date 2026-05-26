"""Reproduce Paper 1, Table 1: Chandler & annual wobble amplitudes by epoch.

Method mirrors the paper's stated procedure:
  - IERS Finals Daily IAU2000 (1973 Jan -> present), final-quality records only
  - Subtract least-squares linear secular drift
  - 3rd-order Butterworth bandpass: 410-470 d (Chandler), 345-390 d (annual)
  - filtfilt zero-phase, Hilbert analytic signal
  - 2D envelope: A(t) = sqrt(Ax(t)^2 + Ay(t)^2)
  - 15% margin exclusion from each end of the dataset (per paper text)

Outputs amplitudes by epoch for direct comparison with Paper 1, Table 1.

DATA: Download finals.all.iau2000.txt from
  https://datacenter.iers.org/data/latestVersion/finals.all.iau2000.txt
and place it next to this script (or set IERS_PATH).
"""
import os
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, hilbert

IERS_PATH = os.environ.get("IERS_PATH", "finals.all.iau2000.txt")


def load_finals(path):
    """Parse IERS Finals Daily fixed-width file -> DataFrame.

    Columns (per IERS Finals format):
      [0:2]   YY
      [2:4]   MM
      [4:6]   DD
      [7:15]  MJD
      [16]    pmflag ('I' final, 'P' predicted, ' ' missing)
      [18:27] PMx (arcsec)
      [37:46] PMy (arcsec)
    """
    rows = []
    with open(path) as f:
        for ln in f:
            if len(ln) < 60:
                continue
            try:
                mjd = float(ln[7:15])
                flag = ln[16]
                pmx_str = ln[18:27].strip()
                pmy_str = ln[37:46].strip()
                if not pmx_str or not pmy_str:
                    continue
                rows.append((mjd, float(pmx_str) * 1000.0, float(pmy_str) * 1000.0, flag))
            except ValueError:
                continue
    df = pd.DataFrame(rows, columns=["mjd", "px_mas", "py_mas", "flag"])
    df["year"] = 2000.0 + (df["mjd"] - 51544.5) / 365.25
    return df.sort_values("mjd").reset_index(drop=True)


def detrend(arr, years):
    coef = np.polyfit(years, arr, 1)
    return arr - (coef[0] * years + coef[1]), coef


def bandpass(signal, fs, lo_d, hi_d, order=3):
    nyq = 0.5 * fs
    lo = (1.0 / hi_d) / nyq
    hi = (1.0 / lo_d) / nyq
    b, a = butter(order, [lo, hi], btype="band")
    return filtfilt(b, a, signal)


def main():
    df = load_finals(IERS_PATH)
    df_final = df[df["flag"] == "I"].reset_index(drop=True)
    print(f"Loaded {len(df_final)} final-quality daily records: "
          f"{df_final['year'].min():.3f} - {df_final['year'].max():.3f}")

    yrs = df_final["year"].values
    px = df_final["px_mas"].values.astype(float)
    py = df_final["py_mas"].values.astype(float)

    px_d, sx = detrend(px, yrs)
    py_d, sy = detrend(py, yrs)
    print(f"Secular drift: slope_x={sx[0]:+.3f} mas/yr, slope_y={sy[0]:+.3f} mas/yr")
    print(f"  => direction {np.degrees(np.arctan2(sy[0], sx[0])):.1f}° W "
          f"at {np.hypot(sx[0], sy[0]):.2f} mas/yr (1973-{df_final['year'].max():.0f})")

    fs = 1.0  # samples per day
    ch_x = bandpass(px_d, fs, 410, 470)
    ch_y = bandpass(py_d, fs, 410, 470)
    an_x = bandpass(px_d, fs, 345, 390)
    an_y = bandpass(py_d, fs, 345, 390)
    ch_env = np.sqrt(np.abs(hilbert(ch_x)) ** 2 + np.abs(hilbert(ch_y)) ** 2)
    an_env = np.sqrt(np.abs(hilbert(an_x)) ** 2 + np.abs(hilbert(an_y)) ** 2)

    n = len(yrs)
    margin = int(0.15 * n)
    inner = np.zeros(n, bool)
    inner[margin:n - margin] = True

    epochs = [(1975, 1985), (1985, 1995), (1995, 2005), (2005, 2010),
              (2010, 2015), (2015, 2020), (2020, 2024), (2024, 2027)]
    print()
    print("Reproduction of Paper 1, Table 1 (15% margin trim applied)")
    print(f"{'Period':<13}{'Chandler (mas)':<22}{'Annual (mas)':<22}{'N':<8}")
    for lo, hi in epochs:
        mask = (yrs >= lo) & (yrs < hi) & inner
        if mask.sum() < 30:
            print(f"{lo}-{hi}     (trimmed by 15% margin - cannot evaluate)")
            continue
        c_m, c_s = ch_env[mask].mean(), ch_env[mask].std()
        a_m, a_s = an_env[mask].mean(), an_env[mask].std()
        print(f"{lo}-{hi}     "
              f"{c_m:6.1f} +/- {c_s:4.1f}        "
              f"{a_m:6.1f} +/- {a_s:4.1f}        "
              f"{mask.sum()}")

    print()
    print("Without margin trim (recent epochs):")
    for lo, hi in [(2018, 2020), (2020, 2022), (2022, 2024), (2024, 2027)]:
        mask = (yrs >= lo) & (yrs < hi)
        if mask.sum() < 30:
            continue
        c = ch_env[mask].mean()
        a = an_env[mask].mean()
        print(f"  {lo}-{hi}: Chandler {c:5.1f} mas, Annual {a:5.1f} mas, N={mask.sum()}")


if __name__ == "__main__":
    main()
