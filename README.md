# Earthquake Analytics on Complex Data

Global USGS earthquakes, M4.5+, Jan 2000 to present.
Techniques: EDA, spatio-temporal preprocessing, ST-DBSCAN, Isolation Forest,
imbalanced classification (class weighting / SMOTE), live data collection.

## Setup
```
pip install -r requirements.txt
```
All shared values live in `scripts/config.py`. In a notebook:
```python
import sys; sys.path.append("../scripts")
from config import *
```

## Layout
```
scripts/    usgs_history.py, usgs_live.py, config.py
data/raw/   raw download (Step 2)        data/live/  live feed (Step 1)
data/processed/  quakes_sample.csv, quakes_clean.csv, cell_month_features.csv
notebooks/  01_download ... 07_live_demo (one step = one notebook)
models/     saved models (.joblib)       figures/  stepX_name.png
results/    every number used in slides/report (.csv)
docs/       data_dictionary.md           slides/ report/ video/
```

## Rules
- Edit only files for the step you own; tell the group before touching others.
- Never use a random train/test split. Split by time per `config.py`.
- Every number in slides/report must come from `results/*.csv`.
- Figures: English, titled, labeled axes with units, saved at `FIG_DPI`.
- Data files are git-ignored; share them via Google Drive.

## Commands
```
python scripts/usgs_live.py --out data/live/live_quakes.csv          # Step 1, keep running (not Colab)
python scripts/usgs_history.py --start 2025-01-01 --end 2026-01-01 --minmag 4.5 --out data/raw/test_2025.csv
python scripts/usgs_history.py --start 2000-01-01 --minmag 4.5 --out data/raw/quakes_m45_raw.csv
```
