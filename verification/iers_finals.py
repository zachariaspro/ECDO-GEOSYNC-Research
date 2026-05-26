"""Shared helper for parsing the IERS Finals Daily IAU2000 fixed-width file.

Used by all the scripts in this folder. Single source of truth for the column
slicing and the MJD -> decimal-year conversion, so a fix here propagates
everywhere instead of having to be applied in five places.

File format reference:
  https://datacenter.iers.org/data/latestVersion/finals.all.iau2000.txt
  https://datacenter.iers.org/eopReadme.txt

Column slices used here (0-indexed Python half-open):
  [7:15]  MJD
  [16]    pmflag ('I' = final, 'P' = predicted, ' ' = missing)
  [18:27] PMx in arcseconds
  [37:46] PMy in arcseconds
"""
import os
import numpy as np
import pandas as pd

DEFAULT_PATH = "finals.all.iau2000.txt"


def load_finals(path=None, only_final=False):
    """Parse the IERS Finals Daily IAU2000 text file.

    Returns a pandas DataFrame with columns:
      mjd        Modified Julian Date (float)
      px_mas     Polar motion x in milliarcseconds
      py_mas     Polar motion y in milliarcseconds
      flag       Quality flag: 'I' (final), 'P' (predicted)
      year       Decimal year, from MJD using MJD 51544.5 == 2000-01-01.5

    Rows missing position data are skipped. Output is sorted by mjd.

    Parameters
    ----------
    path : str or None
        Path to the IERS Finals file. If None, uses $IERS_PATH or
        "finals.all.iau2000.txt" in the current working directory.
    only_final : bool
        If True, drop rows with flag != 'I' (i.e., keep only final-quality
        records).
    """
    if path is None:
        path = os.environ.get("IERS_PATH", DEFAULT_PATH)
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
                rows.append((mjd, float(px_s) * 1000.0, float(py_s) * 1000.0, flag))
            except ValueError:
                continue
    df = pd.DataFrame(rows, columns=["mjd", "px_mas", "py_mas", "flag"])
    df["year"] = 2000.0 + (df["mjd"] - 51544.5) / 365.25
    df = df.sort_values("mjd").reset_index(drop=True)
    if only_final:
        df = df[df["flag"] == "I"].reset_index(drop=True)
    return df


def bearing_label(deg_atan2):
    """Format a bearing computed as degrees(atan2(dy, dx)) in the IERS frame.

    IERS x-axis points to Greenwich, y-axis points to 90 deg W. A positive
    atan2(dy, dx) result therefore corresponds to a bearing west of Greenwich;
    a negative result is east. This function returns a string like '42.8 W' or
    '29.8 E' so the printed table can't be misread.
    """
    if deg_atan2 >= 0:
        return f"{deg_atan2:6.2f} W"
    return f"{abs(deg_atan2):6.2f} E"
