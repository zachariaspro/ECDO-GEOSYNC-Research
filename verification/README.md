# Independent Reproduction Notes

This folder contains a self-contained set of scripts that an interested reader can run against the same IERS Finals Daily product cited by the five papers in this repository. The goal is to make it easy for anyone — author, reviewer, or third party — to reproduce the central numerical results and inspect a few alternative cross-checks.

It is offered in the spirit of constructive peer review, not as a refutation. Where my reproduction differs from the published numbers, I describe what I did and ask whether the discrepancy is genuine or whether I have misread the method.

## Data

All scripts read the IERS Finals Daily IAU2000 series:

```
https://datacenter.iers.org/data/latestVersion/finals.all.iau2000.txt
```

Download once and place it next to the scripts (or set `IERS_PATH`). The series begins 1973-01-02 (MJD 41684) and is updated daily.

## Scripts

| Script | Purpose |
|---|---|
| `01_reproduce_paper1_table1.py` | Apply Paper 1's stated pipeline (Butterworth bandpass + Hilbert envelope, with 15% margin trim) and print amplitudes by epoch. |
| `02_filter_boundary_test.py` | Apply the same pipeline to truncated copies of the dataset and check whether the envelope at a fixed earlier year changes as the endpoint is moved. |
| `03_secular_drift_by_epoch.py` | Linear fit of secular pole drift in (px, py) over user-selected epoch windows, with bearing in degrees-west-of-Greenwich. |
| `04_filter_free_amplitudes.py` | Three independent amplitude estimators with different edge behavior: raw RMS, raw peak-to-peak, and Lomb-Scargle peak. |
| `05_inspect_raw_pole.py` | Prints raw IERS daily pole positions sampled monthly, with no filter at all. |

All scripts are short, dependency-light (numpy, pandas, scipy), and intended to be readable.

## Questions for the author

After running these, I have a few specific questions I'd appreciate the author's view on. None of them is rhetorical — each represents a genuine ambiguity I couldn't resolve from the paper text alone.

### Q1. How does the 15% margin exclusion interact with the 2024-2026 amplitudes?

Paper 1, §2 states "A 15 percent margin is excluded from each analysis window where filter impulse response extends beyond available data ... applied per-period to avoid edge artefacts while preserving recent data."

In my reading, applying a literal 15% margin to a 1973-2026 record removes roughly 1973-1981 and 2018-2026 from the analysis window. But Paper 1 also reports specific Chandler/annual amplitudes for the 2024-2026 epoch (3.5 mas, 3.2 mas in Table 1). 

How is the margin reconciled with reporting values for 2024-2026? Is "applied per-period" referring to a per-component (Chandler vs annual) settling time rather than a percentage of the dataset? If so, what is the actual margin used at the modern end?

### Q2. How is the Butterworth + Hilbert pipeline shown to be stable at the data boundary?

`02_filter_boundary_test.py` finds that the envelope at a fixed year (e.g. 2018) takes different values depending on where the dataset is truncated:

```
Chandler envelope at year 2018:
  data ends 2018  -> 82.5 mas
  data ends 2020  ->  3.5 mas
  data ends 2022  ->  7.9 mas
  data ends 2024  -> 10.5 mas
  data ends 2026  -> 16.9 mas
```

If the envelope is reading a physical property of Earth, the value at 2018 should not depend on what data exists in 2026. Could you describe how the paper distinguishes signal from filtfilt-plus-Hilbert boundary behaviour? In particular, the truncation test described in §2 ("excluding the final 12, 24, and 36 months") — how does it isolate physical attenuation from the fact that any truncation creates a new endpoint at which the same boundary behavior recurs?

### Q3. Cross-check against filter-free estimators

`04_filter_free_amplitudes.py` runs three estimators that have very different edge behavior from filtfilt+Hilbert:

| Method | 1990 | 2018-2020 | 2024-2026 |
|---|---|---|---|
| Raw RMS pole excursion (no bandpass) | 265 mas | 87 mas | 104 mas |
| Raw peak-to-peak range | 540 mas | 200 mas | 250-280 mas |
| Lomb-Scargle Chandler band peak | 231 mas | 50-71 mas | 92-113 mas |
| Lomb-Scargle annual band peak | 209 mas | 87-101 mas | 105-123 mas |
| **Paper 1 reported** | — | — | **3.5 / 3.2 mas** |

These three estimators agree with each other (~100 mas in 2024-2026) and disagree with the paper by a factor of ~30. They all suggest the wobble is at a historic low but not extinct.

Is there a reason these should be discounted relative to the bandpass+Hilbert estimate? Lomb-Scargle in particular is appealing here because it fits sinusoids directly to the data without any zero-phase filter and without assuming periodicity at the data edges.

### Q4. Pole drift direction by epoch

`03_secular_drift_by_epoch.py` fits the IERS Finals Daily series to a linear trend by epoch:

```
1973-1990:  4.4 mas/yr toward  50°W
2000-2005: 10.0 mas/yr toward  65°W
2005-2010: 20.5 mas/yr toward   9°W
2015-2020: 13.9 mas/yr toward  30°E (sign-flipped from W convention)
2020-2026:  5.7 mas/yr toward  14°W
```

This is consistent with the eastward shift reported by Adhikari & Ivins (2016, *Sci. Adv.*) attributed to climate-driven mass redistribution. Paper 2 describes a 75°W forcing direction. Could you clarify whether that direction refers to (a) the long-term GIA-era mean (which was ~80°W and remains a feature of the pre-2000 record), (b) cusp-conditioned hook bearings (a different quantity from the secular trend), or (c) the present-day instantaneous drift direction (which my fits do not show)? The distinction matters for interpreting the convergence claim.

### Q5. Dipole-η correlation

Paper 3 reports `r = 0.97` between IGRF dipole moment and the coupling proxy η over 2005-2025. Both are monotonically declining time series over that window. Was a detrending or first-difference correlation also performed, and if so what was the result? This is a routine check for spurious-trend correlations and would significantly strengthen the causal argument if a residual correlation survives detrending.

### Q6. Raw inspection

`05_inspect_raw_pole.py` prints the IERS daily pole positions sampled monthly through 2026. The peak-to-peak range over the last 18 months in each axis is ~170 mas. Is this range compatible with the paper's reported terminal amplitudes?

## What I do not dispute

- The Chandler wobble has substantially declined since ~2005. This is documented in published work (Yamaguchi & Furuya 2024, Xu et al. 2024, Jeon et al. 2025) and my reproduction reproduces the decline through ~2020.
- The geomagnetic dipole moment has declined by several percent over the past 150 years (IGRF-13).
- The pole drift direction shifted around 2005, as reported by Adhikari & Ivins (2016).
- The 1925-1940 Chandler minimum is documented in the historical record (Höpfner 2004); a comparable second minimum in 2015-2022 is consistent with that history.

## Method summary

The scripts use Python's standard scientific stack (`numpy`, `pandas`, `scipy`). All numerical results above are reproducible from the IERS file alone. The bandpass and Hilbert pipeline used in `01_*` and `02_*` mirrors Paper 1's stated configuration (3rd-order Butterworth, 410-470 d for Chandler, 345-390 d for annual, filtfilt, scipy.signal.hilbert). The filter-free pipeline in `04_*` uses no bandpass and a 4-year sliding window for Lomb-Scargle.
