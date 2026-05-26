"""Direct inspection of recent raw IERS pole positions.

The most assumption-free check on whether the wobble amplitude is currently a few
mas or ~100 mas is to look at the raw daily pole positions over a multi-year window.
A 3-mas wobble would confine the pole to a sub-arc-millisecond patch.
A 100-mas wobble would trace a ~200-mas-diameter spiral.

This script prints one observation per calendar month for years >= START_YEAR
(true monthly sampling, taking the first available record in each month) and
reports the range and standard deviation.
"""
import os

from iers_finals import load_finals

START_YEAR = float(os.environ.get("START_YEAR", "2024.5"))


def main():
    df = load_finals(only_final=True)
    recent = df[df["year"] >= START_YEAR].copy()
    # True monthly sampling: derive year-month from MJD and take first of each month.
    # MJD 51544.5 corresponds to 2000-01-01T12:00. Convert via pandas Timestamp
    # for correctness across leap years.
    import pandas as pd  # local import to keep top of file clean
    recent["date"] = pd.to_datetime(recent["mjd"], unit="D", origin="1858-11-17")
    recent["ym"] = recent["date"].dt.to_period("M")
    monthly = recent.groupby("ym", as_index=False).first()

    print(f"Daily IERS pole positions, first record of each month, "
          f"{START_YEAR:.2f} onward (mas):")
    print(f"  {'year':>8}  {'px':>8}  {'py':>8}")
    for _, r in monthly.iterrows():
        print(f"  {r.year:8.3f}  {r.px_mas:8.1f}  {r.py_mas:8.1f}")
    print()
    print(f"  N months shown: {len(monthly)}")
    print(f"  px range = {monthly.px_mas.max() - monthly.px_mas.min():.0f} mas, "
          f"std = {monthly.px_mas.std():.0f} mas")
    print(f"  py range = {monthly.py_mas.max() - monthly.py_mas.min():.0f} mas, "
          f"std = {monthly.py_mas.std():.0f} mas")


if __name__ == "__main__":
    main()
