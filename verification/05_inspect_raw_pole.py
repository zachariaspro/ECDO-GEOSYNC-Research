"""Direct inspection of recent raw IERS pole positions.

The most assumption-free check on whether the wobble amplitude is currently a few
mas or ~100 mas is to look at the raw daily pole positions over a multi-year window.
A 3-mas wobble would confine the pole to a sub-arc-millisecond patch.
A 100-mas wobble would trace a ~200-mas-diameter spiral.

This script samples the daily px/py monthly from a user-selected start year
and prints the range and standard deviation.
"""
import os
import numpy as np
import pandas as pd

IERS_PATH = os.environ.get("IERS_PATH", "finals.all.iau2000.txt")
START_YEAR = float(os.environ.get("START_YEAR", "2024.5"))


def main():
    rows = []
    with open(IERS_PATH) as f:
        for ln in f:
            if len(ln) < 60:
                continue
            try:
                mjd = float(ln[7:15])
                flag = ln[16]
                px = float(ln[18:27]) * 1000
                py = float(ln[37:46]) * 1000
                if flag == "I":
                    rows.append((mjd, px, py))
            except ValueError:
                continue
    df = pd.DataFrame(rows, columns=["mjd", "px", "py"])
    df["year"] = 2000.0 + (df["mjd"] - 51544.5) / 365.25
    recent = df[df["year"] >= START_YEAR].iloc[::30]

    print(f"Daily IERS pole positions sampled monthly, {START_YEAR:.2f} onward (mas):")
    print(f"  {'year':>8}  {'px':>8}  {'py':>8}")
    for _, r in recent.iterrows():
        print(f"  {r.year:8.3f}  {r.px:8.1f}  {r.py:8.1f}")
    print()
    print(f"  N samples shown: {len(recent)}")
    print(f"  px range = {recent.px.max() - recent.px.min():.0f} mas, "
          f"std = {recent.px.std():.0f} mas")
    print(f"  py range = {recent.py.max() - recent.py.min():.0f} mas, "
          f"std = {recent.py.std():.0f} mas")


if __name__ == "__main__":
    main()
