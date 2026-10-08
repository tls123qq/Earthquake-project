# Data dictionary: quakes_clean.csv

Filled in during Step 3. Columns are locked: append new ones at the end only.

| Column | Type | Nullable | Meaning |
|---|---|---|---|
| id | str | no | Unique event ID |
| time | datetime (UTC) | no | Origin time |
| year, month | int | no | From `time` |
| latitude, longitude | float | no | Coordinates |
| depth | float (km) | no | Depth |
| depth_class | str | no | shallow (<70), intermediate (70-300), deep (>300) |
| depth_fixed | bool | no | Depth likely a default value, not measured |
| mag | float | no | Magnitude |
| magType | str | no | Magnitude scale (mb, mww, ...) |
| is_major | int (0/1) | no | `mag >= MAJOR_MAG` |
| region | str | yes | Country/region parsed from `place` |
| cell_id | str | no | Grid cell per `GRID_DEG`, e.g. "10_95" |
| nst, gap, rms, dmin, horizontalError, depthError, magError, magNst | float | yes | Measurement-quality columns (not imputed) |
