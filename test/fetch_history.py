"""Test run: download the full USGS M4.5+ earthquake history into this folder.

Yearly chunks (split in half if a chunk hits the 20,000-event cap),
per-chunk cache in ./chunks so a rerun resumes, merged into one CSV.
"""
import io
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

QUERY = "https://earthquake.usgs.gov/fdsnws/event/1/query"
COUNT = "https://earthquake.usgs.gov/fdsnws/event/1/count"
MAX_EVENTS = 20000
MIN_MAG = 4.5
START = datetime(2000, 1, 1, tzinfo=timezone.utc)

HERE = Path(__file__).resolve().parent
CHUNKS = HERE / "chunks"
OUT = HERE / "quakes_m45_raw.csv"


def params(start, end):
    return {
        "starttime": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": MIN_MAG,
        "eventtype": "earthquake",
        "orderby": "time-asc",
    }


def get(url, p, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, params=p, timeout=300)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if i == tries - 1:
                raise
            wait = 5 * (i + 1)
            print(f"    retry in {wait}s ({e})")
            time.sleep(wait)


def fetch_range(start, end):
    """Return list of chunk files covering [start, end)."""
    path = CHUNKS / f"{start:%Y%m%dT%H%M%S}_{end:%Y%m%dT%H%M%S}.csv"
    if path.exists():
        return [path]
    n = int(get(COUNT, {**params(start, end), "format": "text"}).text.strip())
    if n >= MAX_EVENTS:
        mid = start + (end - start) / 2
        print(f"  {start:%Y-%m-%d}..{end:%Y-%m-%d}: {n} events -> split")
        return fetch_range(start, mid) + fetch_range(mid, end)
    t = time.time()
    r = get(QUERY, {**params(start, end), "format": "csv"})
    path.write_bytes(r.content)
    print(f"  {start:%Y-%m-%d}..{end:%Y-%m-%d}: {n:>6} events, "
          f"{len(r.content) / 1e6:5.2f} MB, {time.time() - t:5.2f}s")
    time.sleep(1)  # be polite to USGS
    return [path]


def main():
    CHUNKS.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    t0 = time.time()
    files = []
    for year in range(START.year, now.year + 1):
        s = datetime(year, 1, 1, tzinfo=timezone.utc)
        e = min(datetime(year + 1, 1, 1, tzinfo=timezone.utc), now)
        files += fetch_range(s, e)

    df = pd.concat(
        (pd.read_csv(f, encoding="utf-8") for f in files if f.stat().st_size > 0),
        ignore_index=True,
    )
    before = len(df)
    df = (df.sort_values("updated")
            .drop_duplicates("id", keep="last")
            .sort_values("time")
            .reset_index(drop=True))
    df.to_csv(OUT, index=False, encoding="utf-8")

    print(f"\nDone in {time.time() - t0:.1f}s")
    print(f"rows: {before} -> {len(df)} after dedup by id")
    print(f"time range: {df['time'].min()} .. {df['time'].max()}")
    print(f"saved: {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
