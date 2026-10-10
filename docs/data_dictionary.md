# Data dictionary: quakes_clean.csv

Made by `notebooks/02_preprocess.ipynb` (Step 3) from `data/raw/quakes_m45_raw.csv`.
All numbers below come from `results/step3_*.csv` (raw file updated to 2026-10-10).
Columns are locked: append new ones at the end only.

- Rows: **187,547** (187,588 raw rows, 41 removed), one row per earthquake
- Period: 2000-01-01 to 2026-10-10 (UTC), M4.5+, worldwide
- `quakes_sample.csv` has the same columns, years 2024-2025 only (14,952 rows)

Read it with: `pd.read_csv(CLEAN_FILE, parse_dates=["time"])`

| Column | Type | Nullable | Meaning |
|---|---|---|---|
| id | str | no | USGS event id, unique |
| time | datetime (UTC) | no | Origin time, written as `2026-10-01T21:01:41.707000Z` |
| year, month | int | no | From `time` |
| latitude, longitude | float (degrees) | no | Epicentre |
| depth | float (km) | no | Depth. 12 rows are slightly negative (above sea level) and are kept |
| depth_class | str | no | `shallow` (< 70 km), `intermediate` (70 to < 300 km), `deep` (>= 300 km): 148,239 / 30,621 / 8,687 rows |
| depth_fixed | bool | no | Depth is a default value, not a measurement: depth is exactly 10, 30, 33, 35 km. True for 87,087 rows (46.4%) |
| mag | float | no | Magnitude, >= 4.5. Scales are **not** converted to a common one |
| magType | str | no | Magnitude scale, lower-cased (19 scales; `mb` is 78.5%) |
| is_major | int (0/1) | no | `mag >= MAJOR_MAG` (6.5). 1 for 1,218 rows (0.65%) |
| region | str | yes (0 missing now) | Country, US state or sea area parsed from the raw `place` text (439 values) |
| cell_id | str | no | 5 degree grid cell from floored coordinates, e.g. `"10_95"` = lat 10 to 15, lon 95 to 100 (1,206 cells have events) |
| nst, gap, rms, dmin, horizontalError, depthError, magError, magNst | float | **yes** | Measurement-quality columns, copied from the raw file and **not imputed** |

## How each derived column was made

- **depth_fixed**: a whole-km depth is a default when its row count is at least 10 times the median
  count of the neighbouring whole-km depths (within 5 km) and at least 1,000 rows. See
  `results/step3_depth_spikes.csv`. Smaller spikes at round deep values (for example 600 km) are not flagged.
- **region**: text after the last comma of `place` (`"2 km NE of Satte, Japan"` -> `Japan`), with a
  trailing `region` or `Earthquake` removed and `CA, AK, NV, OR, MX` written out. 23.2% of places
  have no comma (offshore areas such as `"south of the Fiji Islands"`); for those the area name is used
  after removing the direction words (-> `Fiji Islands`). Names are not merged further, so `Fiji` and
  `Fiji Islands` are separate values.
- **cell_id**: `config.cell_id()`. Longitude is not wrapped at the date line.

## Rows removed (see `results/step3_summary.csv`)

- 4 rows with `mag` below 4.5 (USGS revised them down after we downloaded them)
- 37 rows that are a second id for an earthquake already in the file (at most 10 s and 10 km
  apart). The row with the **larger magnitude** is kept. Keeping the newest `updated` instead would have
  kept the smaller row in 11 cases and removed 3 major earthquakes. All pairs are in
  `results/step3_duplicate_pairs.csv`.
- 0 deleted events, 0 non-earthquakes, 0 rows with a missing core value, 0 repeated ids.

## Missing values in the quality columns (% of clean rows)

| nst | gap | rms | dmin | horizontalError | depthError | magError | magNst |
|---|---|---|---|---|---|---|---|
| 35.9% | 9.2% | 2.6% | 48.0% | 51.9% | 29.9% | 48.8% | 15.3% |

They are missing by catalog era and by reporting network, not at random
(`figures/step3_missing_by_year.png`): `dmin`, `horizontalError` and `magError` are almost never present
before 2013, and `nst` is missing for almost all of 2014-2021. Do not fill them with an average, and
do not use them as model features across the time-based train/test split.
