"""ดึงข้อมูลแผ่นดินไหวจาก USGS ลงไฟล์ CSV ไฟล์เดียว (ย้อนหลัง + ข้อมูลสด)

ทุกรอบ: อ่านไฟล์เดิม -> ถาม USGS ว่ามีเหตุการณ์ไหนใหม่หรือถูกแก้หลังค่า `updated`
ล่าสุดในไฟล์ -> id ใหม่เพิ่มแถว, id เดิมแทนด้วยแถวที่ใหม่กว่า -> เขียนไฟล์ใหม่
ถ้ายังไม่มีไฟล์ จะดึงย้อนหลังตั้งแต่ --start ทีละปีก่อน

ใช้แค่ standard library ไม่ต้องติดตั้งอะไรเพิ่ม

ตัวอย่าง:
    # รันรอบเดียว
    python scripts/usgs_fetch.py
    # เก็บข้อมูลสด วนทุก 5 นาที (กด Ctrl+C เพื่อหยุด)
    python scripts/usgs_fetch.py --loop 300
"""

import argparse
import csv
import io
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# ให้ import config.py ที่อยู่โฟลเดอร์เดียวกันได้ ไม่ว่าจะรันจากโฟลเดอร์ไหน
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import MIN_MAG, RAW_FILE, START_DATE  # noqa: E402

API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
API_LIMIT = 20000  # USGS ให้ไม่เกิน 20,000 แถวต่อครั้ง
USER_AGENT = "earthquake-class-project/1.0"

USGS_COLUMNS = [
    "time", "latitude", "longitude", "depth", "mag", "magType", "nst", "gap",
    "dmin", "rms", "net", "id", "updated", "place", "type", "horizontalError",
    "depthError", "magError", "magNst", "status", "locationSource", "magSource",
]
EXTRA_COLUMNS = ["first_seen_at", "last_fetched_at"]
COLUMNS = USGS_COLUMNS + EXTRA_COLUMNS

# ถอยเวลา updatedafter ไว้นิดหน่อย กันพลาดเหตุการณ์ที่ updated ตรงกับค่าล่าสุดพอดี
# แถวที่ได้ซ้ำมาจะถูกเทียบ `updated` แล้วข้ามไปเอง
OVERLAP = timedelta(minutes=10)
KEEP_BACKUPS = 3


def log(msg):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{stamp}] {msg}", flush=True)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def to_api_time(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


# ---------- ไฟล์ ----------

def load(path):
    """อ่านไฟล์เดิมเป็น (dict {id: row}, ต้องเพิ่มคอลัมน์ไหม) ถ้ายังไม่มีไฟล์คืน (None, False)"""
    if not os.path.exists(path):
        return None, False
    # แถวจากไฟล์ที่ดึงก่อนมีสคริปต์นี้ ไม่มี first_seen_at ให้ใช้เวลาที่ไฟล์ถูกแก้ล่าสุดแทน
    mtime = datetime.fromtimestamp(os.path.getmtime(path), timezone.utc)
    fallback = mtime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        upgrade = any(c not in (reader.fieldnames or []) for c in EXTRA_COLUMNS)
        for row in reader:
            for col in EXTRA_COLUMNS:
                if not row.get(col):
                    row[col] = fallback
            rows[row["id"]] = row
    return rows, upgrade


def save(path, rows):
    """เขียนลงไฟล์ชั่วคราวก่อน แล้วค่อยแทนไฟล์จริง กันไฟล์เสียถ้าดับกลางทาง"""
    tmp = path + ".tmp"
    ordered = sorted(rows.values(), key=lambda r: r["time"])
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered)
    os.replace(tmp, path)


def backup(path, backup_dir):
    """สำรองไฟล์วันละครั้ง เก็บไว้แค่ KEEP_BACKUPS ไฟล์ล่าสุด"""
    if not os.path.exists(path):
        return
    os.makedirs(backup_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    target = os.path.join(backup_dir, f"{base}_{day}.csv")
    if os.path.exists(target):
        return
    shutil.copy2(path, target)
    log(f"สำรองไฟล์ -> {target}")
    old = sorted(f for f in os.listdir(backup_dir) if f.startswith(base + "_"))
    for name in old[:-KEEP_BACKUPS]:
        os.remove(os.path.join(backup_dir, name))


# ---------- API ----------

def request_csv(params, retries=3):
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                text = resp.read().decode("utf-8")
            return list(csv.DictReader(io.StringIO(text)))
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == retries:
                raise
            log(f"เรียก API ไม่สำเร็จ ({e}) ลองใหม่ครั้งที่ {attempt + 1}")
            time.sleep(10 * attempt)


def fetch_all(params):
    """ดึงทุกหน้า (ทีละ API_LIMIT แถว) ด้วย offset"""
    out, offset = [], 1
    while True:
        page = request_csv({**params, "limit": API_LIMIT, "offset": offset})
        out.extend(page)
        if len(page) < API_LIMIT:
            return out
        offset += API_LIMIT


def backfill(start, minmag):
    """ดึงย้อนหลังทีละปี ตั้งแต่ start จนถึงตอนนี้"""
    rows = {}
    now = datetime.now(timezone.utc)
    year = start.year
    t0 = start
    while t0 < now:
        t1 = min(datetime(year + 1, 1, 1, tzinfo=timezone.utc), now)
        batch = fetch_all({
            "format": "csv", "eventtype": "earthquake", "minmagnitude": minmag,
            "starttime": to_api_time(t0), "endtime": to_api_time(t1),
            "orderby": "time-asc",
        })
        for r in batch:
            rows[r["id"]] = r
        log(f"ย้อนหลัง {year}: {len(batch):,} แถว (รวม {len(rows):,})")
        year += 1
        t0 = t1
    return rows


def fetch_updates(since, start, minmag):
    """เหตุการณ์ที่ใหม่ ถูกแก้ หรือถูกลบ หลังเวลา since"""
    params = {
        "format": "csv", "minmagnitude": minmag,
        "starttime": to_api_time(start),  # ถ้าไม่ใส่ API จะค้นแค่ 30 วันล่าสุด
        "updatedafter": to_api_time(since - OVERLAP),
        "orderby": "time-asc",
    }
    updates = fetch_all({**params, "eventtype": "earthquake"})
    # เหตุการณ์ที่ถูกลบต้องถามแยก: includedeleted=true ช้าจน timeout ถ้าย้อนเกินราว 1 วัน
    # ส่วน includedeleted=only เร็ว และแถวที่ถูกลบมี type ว่าง จึงกรอง eventtype ไม่ได้
    deleted = fetch_all({**params, "includedeleted": "only"})
    return updates + deleted


# ---------- รวมข้อมูล ----------

def merge(rows, updates, minmag):
    """รวม updates เข้า rows คืนจำนวน (ใหม่, ถูกแก้, ถูกลบ)"""
    stamp = now_iso()
    added = changed = deleted = 0
    for new in updates:
        eid = new["id"]
        old = rows.get(eid)
        is_deleted = new.get("status") == "deleted"
        if old is None:
            # รอบอัปเดตดึงด้วย minmag ต่ำกว่าเกณฑ์ เพื่อจับเหตุการณ์ที่ถูกแก้ขนาดลง
            # แต่เหตุการณ์ใหม่ที่ต่ำกว่าเกณฑ์หรือถูกลบไปแล้ว ไม่ต้องเก็บ
            if is_deleted or not new.get("mag") or float(new["mag"]) < minmag:
                continue
            new["first_seen_at"] = stamp
            new["last_fetched_at"] = stamp
            rows[eid] = new
            added += 1
            continue
        if parse_iso(new["updated"]) <= parse_iso(old["updated"]):
            continue  # ได้ซ้ำมาจากช่วง OVERLAP
        if is_deleted:
            # แถวที่ถูกลบมักไม่มีค่าอื่นมาด้วย เก็บค่าเดิมไว้ เปลี่ยนแค่สถานะ
            old["status"] = "deleted"
            old["updated"] = new["updated"]
            old["last_fetched_at"] = stamp
            deleted += 1
            continue
        new["first_seen_at"] = old["first_seen_at"]
        new["last_fetched_at"] = stamp
        rows[eid] = new
        changed += 1
    return added, changed, deleted


def run_once(args):
    rows, upgrade = load(args.out)
    if not rows:
        log(f"ยังไม่มี {args.out} เริ่มดึงย้อนหลังตั้งแต่ {args.start:%Y-%m-%d}")
        rows = backfill(args.start, args.minmag)
        stamp = now_iso()
        for r in rows.values():
            r["first_seen_at"] = r["last_fetched_at"] = stamp
        save(args.out, rows)
        log(f"บันทึก {len(rows):,} แถว -> {args.out}")
        # ดึงต่อทันที เผื่อมีเหตุการณ์ถูกแก้ระหว่างที่ดึงย้อนหลัง

    since = max(parse_iso(r["updated"]) for r in rows.values())
    updates = fetch_updates(since, args.start, args.update_minmag)
    added, changed, deleted = merge(rows, updates, args.minmag)
    log(f"ได้จาก API {len(updates):,} แถว -> ใหม่ {added}, ถูกแก้ {changed}, "
        f"ถูกลบ {deleted} (รวม {len(rows):,})")

    if added or changed or deleted or upgrade:
        backup(args.out, args.backup_dir)
        save(args.out, rows)


def main():
    # ให้ข้อความภาษาไทยอ่านได้ แม้จะส่งต่อไปเก็บในไฟล์ log
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default=str(RAW_FILE),
                   help="ไฟล์ข้อมูล (ค่าเริ่มต้น: RAW_FILE ใน config.py)")
    p.add_argument("--start", default=START_DATE,
                   type=lambda s: datetime.fromisoformat(s).replace(tzinfo=timezone.utc),
                   help="ดึงข้อมูลตั้งแต่วันไหน (ค่าเริ่มต้น: START_DATE ใน config.py)")
    p.add_argument("--minmag", type=float, default=MIN_MAG,
                   help="ขนาดขั้นต่ำของเหตุการณ์ที่เก็บ (ค่าเริ่มต้น: MIN_MAG ใน config.py)")
    p.add_argument("--update-minmag", type=float, default=None,
                   help="ขนาดขั้นต่ำตอนดึงอัปเดต ต่ำกว่า --minmag เพื่อจับเหตุการณ์ที่ถูกแก้ขนาดลง "
                        "(ค่าเริ่มต้น: --minmag ลบ 0.5)")
    p.add_argument("--loop", type=int, default=0, metavar="SECONDS",
                   help="วนซ้ำทุกกี่วินาที (0 = รันรอบเดียว)")
    p.add_argument("--backup-dir", default=None,
                   help="โฟลเดอร์สำรองไฟล์ (ค่าเริ่มต้น: <โฟลเดอร์ของ --out>/backup)")
    args = p.parse_args()
    if args.update_minmag is None:
        args.update_minmag = args.minmag - 0.5
    if args.backup_dir is None:
        args.backup_dir = os.path.join(os.path.dirname(args.out) or ".", "backup")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    if not args.loop:
        run_once(args)
        return

    log(f"เริ่มเก็บข้อมูลสด ทุก {args.loop} วินาที (Ctrl+C เพื่อหยุด)")
    while True:
        try:
            run_once(args)
        except KeyboardInterrupt:
            raise
        except PermissionError as e:
            # Windows: ถ้าเปิดไฟล์ค้างใน Excel จะเขียนทับไม่ได้ รอบหน้าจะลองใหม่
            log(f"เขียนไฟล์ไม่ได้ ({e}) ปิดไฟล์ใน Excel แล้วรอรอบถัดไป")
        except Exception as e:
            log(f"ผิดพลาด: {e!r} จะลองใหม่รอบถัดไป")
        time.sleep(args.loop)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("หยุดแล้ว")
        sys.exit(0)
