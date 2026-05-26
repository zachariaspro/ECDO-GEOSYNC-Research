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

Lomb-Scargle scaling convention
-------------------------------
scipy.signal.lombscargle with normalize=False returns power P(omega). For a
real signal x_n = A * cos(omega_0 t_n) sampled at N points, the periodogram at
omega_0 evaluates to approximately P = N * A^2 / 4 (asymptotic; exact value
depends on sampling). For a 2D circular signal (px = A cos, py = A sin), the
sum Px + Py = N * A^2 / 2, so the 2D amplitude is recovered as

    A_2D = sqrt(2 * (Px + Py) / N)

This is what `lomb_amp_2d()` below computes, and the calibration test
`_calibrate_lombscargle()` runs at startup confirms the recovered amplitude on
a synthetic circular signal of known amplitude.
"""
import numpy as np
import pandas as pd
from scipy.signal import lombscargle

from iers_finals import load_finals


def lomb_amp_2d(t, sx, sy, ang_freqs):
    """Return 2D Lomb-Scargle peak amplitude over a vector of angular frequencies.

    See the module docstring for the scaling derivation.
    """
    N = len(t)
    Px = lombscargle(t, sx, ang_freqs, normalize=False)
    Py = lombscargle(t, sy, ang_freqs, normalize=False)
    return np.sqrt(2.0 * (Px + Py).max() / N)


def _calibrate_lombscargle():
    """Sanity-check the lomb_amp_2d scaling on a synthetic signal.

    Builds a 2D circular oscillation of known amplitude at the Chandler period
    and confirms that lomb_amp_2d recovers it. Raises AssertionError on failure
    so a future SciPy convention change can't silently break the amplitude
    units in the table below.
    """
    rng = np.random.default_rng(0)
    A_true = 100.0
    period = 433.0
    N = 365 * 4
    t = np.arange(N).astype(float) + rng.uniform(0, 1, N)
    sx = A_true * np.cos(2 * np.pi * t / period)
    sy = A_true * np.sin(2 * np.pi * t / period)
    ang = np.linspace(2 * np.pi / 470, 2 * np.pi / 410, 50)
    A_rec = lomb_amp_2d(t, sx, sy, ang)
    assert abs(A_rec - A_true) < 1.0, (
        f"Lomb-Scargle amplitude calibration failed: "
        f"true {A_true}, recovered {A_rec:.2f}. "
        f"Check SciPy convention for lombscargle(normalize=False)."
    )


def main():
    _calibrate_lombscargle()

    df = load_finals(only_final=True)
    y = df["year"].values
    px = df["px_mas"].values.astype(float)
    py = df["py_mas"].values.astype(float)
    cx = np.polyfit(y, px, 1)
    cy = np.polyfit(y, py, 1)
    px -= cx[0] * y + cx[1]
    py -= cy[0] * y + cy[1]

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
    ang_chand = 2 * np.pi / np.linspace(410, 470, 30)
    ang_ann = 2 * np.pi / np.linspace(345, 390, 30)
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
        A_c = lomb_amp_2d(t, sx, sy, ang_chand)
        A_a = lomb_amp_2d(t, sx, sy, ang_ann)
        print(f"{yc:6}        {A_c:10.1f}              {A_a:10.1f}")


if __name__ == "__main__":
    main()
