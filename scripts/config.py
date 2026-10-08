"""Shared settings for every step. Change only after the whole group agrees."""
from pathlib import Path

# --- Agreed project values (from the plan) ---
START_DATE   = "2000-01-01"
MIN_MAG      = 4.5
MAJOR_MAG    = 6.5          # threshold for "major earthquake"
GRID_DEG     = 5            # grid cell size (degrees)
TRAIN_END    = "2019-12-31" # time-based split, never random
VAL_END      = "2022-12-31" # 2023 onward = test
RANDOM_STATE = 42
FIG_DPI      = 200

# --- Paths (so every notebook reads/writes the same files) ---
ROOT          = Path(__file__).resolve().parents[1]
DATA_RAW      = ROOT / "data" / "raw"
DATA_LIVE     = ROOT / "data" / "live"
DATA_PROC     = ROOT / "data" / "processed"
MODELS_DIR    = ROOT / "models"
FIGURES_DIR   = ROOT / "figures"
RESULTS_DIR   = ROOT / "results"

RAW_FILE      = DATA_RAW  / "quakes_m45_raw.csv"
LIVE_FILE     = DATA_LIVE / "live_quakes.csv"
SAMPLE_FILE   = DATA_PROC / "quakes_sample.csv"
CLEAN_FILE    = DATA_PROC / "quakes_clean.csv"
FEATURES_FILE = DATA_PROC / "cell_month_features.csv"

# --- Locked columns of quakes_clean.csv (append only, never rename/remove) ---
CLEAN_COLUMNS = [
    "id", "time", "year", "month", "latitude", "longitude", "depth",
    "depth_class", "depth_fixed", "mag", "magType", "is_major", "region",
    "cell_id", "nst", "gap", "rms", "dmin", "horizontalError",
    "depthError", "magError", "magNst",
]
DEPTH_BINS = {"shallow": (0, 70), "intermediate": (70, 300), "deep": (300, None)}


def cell_id(lat, lon, grid=GRID_DEG):
    """Grid cell from floored coordinates, e.g. (12.3, 98.7) -> '10_95'."""
    import math
    return f"{int(math.floor(lat / grid) * grid)}_{int(math.floor(lon / grid) * grid)}"
