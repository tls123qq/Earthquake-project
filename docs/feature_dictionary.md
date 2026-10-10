# Feature dictionary: cell_month_features.csv (Step 7)

Built by `notebooks/06_classification.ipynb` (part 1) from `quakes_clean.csv`.

- **One row** = one grid cell (`GRID_DEG` = 5°) × one calendar month `t`.
- **Cells:** every cell with at least one event (1,204 cells; the 2 events at longitude exactly 180° are merged into the matching `_-180` cell so the grid wraps at the date line).
- **Months:** 2000-01 up to the month before the last complete month, because the last complete month can only be a target.
- **All features use events in month `t` or earlier.** This is checked in the notebook by rebuilding the features without any data after a cutoff and confirming nothing changes (`results/step7_leakage_checks.csv`).

## Identifier columns

| Column | Type | Meaning |
|---|---|---|
| `cell_id` | str | Grid cell, e.g. `"35_140"` (lower-left corner, degrees) |
| `cell_lat`, `cell_lon` | int | Lower-left corner of the cell |
| `month` | str `YYYY-MM` | Month `t` the features describe |
| `target_month` | str `YYYY-MM` | Month `t+1` the target describes |
| `split` | str | `train` / `val` / `test`, decided by `target_month` vs `TRAIN_END` and `VAL_END` |

## Features (15)

| Column | Type | Meaning |
|---|---|---|
| `n_events_1m` | int | Events in the cell in month `t` |
| `n_events_3m` | int | Events in months `t-2` to `t` |
| `n_events_12m` | int | Events in months `t-11` to `t` |
| `n_major_12m` | int | Events with M ≥ `MAJOR_MAG` in months `t-11` to `t` (the naive baseline predicts 1 when this is ≥ 1) |
| `max_mag_12m` | float | Largest magnitude in months `t-11` to `t` (0 if no event) |
| `months_since_major` | int | Months since the last major in the cell, capped at 120 (also 120 if there has never been one) |
| `had_major_before` | 0/1 | 1 if the cell has had any major from 2000 up to `t` |
| `n_events_hist` | int | All events in the cell from 2000 up to `t` |
| `mean_depth_hist` | float (km) | Mean depth of all events up to `t` (0 if none yet) |
| `frac_shallow_hist` | float | Share of events up to `t` with `depth_class = shallow` |
| `frac_intermediate_hist` | float | Share with `depth_class = intermediate` |
| `frac_deep_hist` | float | Share with `depth_class = deep` |
| `nbr_events_1m` | int | Events in the 8 surrounding cells in month `t` (longitude wraps at ±180°, latitude does not) |
| `nbr_events_12m` | int | Events in the 8 surrounding cells in months `t-11` to `t` |
| `nbr_major_12m` | int | Majors in the 8 surrounding cells in months `t-11` to `t` |

## Target

| Column | Type | Meaning |
|---|---|---|
| `y` | 0/1 | 1 if `target_month` has at least one event with M ≥ `MAJOR_MAG` in the cell |

Per-event measurement columns (`nst`, `gap`, `magType`, `magError`, ...) are never used, because they are produced together with the magnitude and would leak the answer.

## Known limitation

The cell list uses all data (a cell is included if it ever had an event). 98 cells had their first event after `TRAIN_END`. This selects which cells appear, but does not change any feature value.
