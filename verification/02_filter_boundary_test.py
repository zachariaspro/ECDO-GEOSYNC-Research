"""Test how the bandpass-Hilbert amplitude estimate depends on dataset endpoint.

Premise: if the wobble amplitude at year Y is a physical property of Earth at year Y,
it should not depend on whether the dataset we analyse ends at year Y, Y+2, Y+4, etc.

Procedure:
  - Reproduce Paper 1's bandpass-Hilbert pipeline on the IERS Finals Daily series.
  - For each truncation endpoint T in {2018, 2020, 2022, 2024, 2026, latest}, compute
    Chandler and annual envelopes.
  - Compare the envelope value at fixed earlier epochs Y across all truncations.

A stable physical signal should give the same A(Y) regardless of T (for T > Y).
A boundary-induced behaviour will give different A(Y) for different T.

This script does not claim either outcome a priori; it just lays out the comparison.
"""
import os
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, hilbert

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


def envelope(df_slice):
    y = df_slice["year"].values
    px = df_slice["px"].values.astype(float).copy()
    py = df_slice["py"].values.astype(float).copy()
    cx = np.polyfit(y, px, 1)
    cy = np.polyfit(y, py, 1)
    px -= cx[0] * y + cx[1]
    py -= cy[0] * y + cy[1]

    def bp(s, lo_d, hi_d):
        nyq = 0.5
        b, a = butter(3, [(1 / hi_d) / nyq, (1 / lo_d) / nyq], btype="band")
        return filtfilt(b, a, s)

    ch = np.sqrt(np.abs(hilbert(bp(px, 410, 470))) ** 2 +
                 np.abs(hilbert(bp(py, 410, 470))) ** 2)
    an = np.sqrt(np.abs(hilbert(bp(px, 345, 390))) ** 2 +
                 np.abs(hilbert(bp(py, 345, 390))) ** 2)
    return y, ch, an


def main():
    df = load_finals(IERS_PATH)
    truncs = [2018.0, 2020.0, 2022.0, 2024.0, 2026.0, df["year"].max()]
    cache = {}
    for t in truncs:
        cache[t] = envelope(df[df["year"] <= t].reset_index(drop=True))

    test_years = [2010.0, 2013.0, 2015.0, 2018.0, 2020.0, 2022.0, 2024.0]

    def report(label, get):
        print(label)
        header = "year   " + "  ".join(f"end={t:6.2f}" for t in truncs)
        print(header)
        for ty in test_years:
            line = f"{ty:5.1f}  "
            for t in truncs:
                y, _, _ = cache[t]
                if y.max() < ty - 0.05:
                    line += "      n/a    "
                    continue
                i = np.argmin(np.abs(y - ty))
                if abs(y[i] - ty) > 0.05:
                    line += "      n/a    "
                else:
                    line += f"  {get(t)[i]:6.1f} mas "
            print(line)
        print()

    report("Chandler envelope at fixed year, by dataset endpoint",
           lambda t: cache[t][1])
    report("Annual envelope at fixed year, by dataset endpoint",
           lambda t: cache[t][2])

    # Show the U-shape near the actual data edge
    print("Envelope value vs. distance from end of latest dataset:")
    y, ch, an = cache[df["year"].max()]
    for ybe in [0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0]:
        i = np.argmin(np.abs(y - (y.max() - ybe)))
        print(f"  {ybe:4.2f} yr before end (year {y[i]:.2f}): "
              f"Chandler {ch[i]:6.1f}, Annual {an[i]:6.1f}")


if __name__ == "__main__":
    main()
