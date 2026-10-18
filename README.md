# Earthquake Analytics on Complex Data

วิเคราะห์ข้อมูลแผ่นดินไหวทั่วโลกจาก USGS ขนาด 4.5 ขึ้นไป ตั้งแต่ ม.ค. 2000 ถึงปัจจุบัน
เทคนิคที่ใช้: EDA, การเตรียมข้อมูลเชิงพื้นที่และเวลา, ST-DBSCAN, Isolation Forest,
imbalanced classification (class weight / SMOTE) และการเก็บข้อมูลสด

## วิธีรัน (ทีละขั้น)

ทดสอบกับ Python 3.14 บน Windows (pandas 3.0, scikit-learn 1.9, LightGBM 4.7)
ทุกคำสั่งรันจากโฟลเดอร์หลักของโปรเจกต์

**1. ดาวน์โหลดโค้ดและติดตั้ง library**
```
git clone https://github.com/tls123qq/Earthquake-project.git
cd Earthquake-project
pip install -r requirements.txt
```

**2. (ไม่บังคับ) ดึงข้อมูลล่าสุดจาก USGS**

ใน repo มี `data/raw/quakes_m45_raw.csv` อยู่แล้ว (ข้อมูลถึง 2026-10-10 ซึ่งเป็นชุดที่ใช้ทำผลทั้งหมด)
ถ้าต้องการได้ผลตรงกับรายงาน ให้ข้ามขั้นนี้ รันเฉพาะเมื่ออยากได้เหตุการณ์ใหม่:
```
python scripts/usgs_fetch.py
```
ถ้าในโฟลเดอร์ยังไม่มีไฟล์ข้อมูล ครั้งแรกจะดึงทั้งหมดตั้งแต่ปี 2000 (ใช้เวลาหลายนาที)
ครั้งต่อไปจะดึงเฉพาะเหตุการณ์ที่ใหม่หรือถูกแก้ไข

**3. รัน notebook ตามลำดับ**

เปิดใน Jupyter หรือ VS Code แล้วกด *Run All* ทีละตัว หรือรันทั้งหมดด้วยคำสั่งเดียว
(แต่ละ notebook จะเขียนทับผลลัพธ์ของตัวเอง):
```
cd notebooks
python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 02_preprocess.ipynb 03_eda.ipynb 04_clustering.ipynb 05_anomaly.ipynb 06_classification.ipynb 07_live_demo.ipynb
```

| ลำดับ | Notebook | Step | อ่าน | เขียน | เวลา* |
|---|---|---|---|---|---|
| 1 | `01_download.ipynb` | 1-2 | (ไม่ต้องรัน ข้อมูลมาจาก `usgs_fetch.py`) | - | - |
| 2 | `02_preprocess.ipynb` | 3 ทำความสะอาดข้อมูล | `data/raw/quakes_m45_raw.csv` | `data/processed/quakes_clean.csv`, `quakes_sample.csv`, `figures/step3_*`, `results/step3_*` | 20 วินาที |
| 3 | `03_eda.ipynb` | 4 สำรวจข้อมูล | `quakes_clean.csv` | `figures/step4_*`, `results/eda_summary.csv`, `known_events.csv`, `step4_*` | 10 วินาที |
| 4 | `04_clustering.ipynb` | 5 ST-DBSCAN | `quakes_clean.csv` | `figures/step5_*`, `results/step5_*`, `clusters_summary.csv` | 2 นาที |
| 5 | `05_anomaly.ipynb` | 6 Isolation Forest | `quakes_clean.csv` | `models/isoforest.joblib`, `figures/step6_*`, `results/anomaly_metrics.csv`, `step6_*` | 30 วินาที |
| 6 | `06_classification.ipynb` | 7-9 ตาราง feature, โมเดล, วัดผล | `quakes_clean.csv` | `data/processed/cell_month_features.csv`, `figures/step7_*`, `step9_*`, `results/classification_metrics.csv`, `step7_*` ถึง `step9_*` | 3 นาที |
| 7 | `07_live_demo.ipynb` | 10 Live demo | ไฟล์ raw, `models/isoforest.joblib` | `figures/step10_*` (รวม `step10_live_replay.html`), `results/step10_*` | 15 วินาที |

\* บนโน้ตบุ๊กทั่วไป

ต้องรัน 02 ก่อน ตัว 03 ถึง 06 ใช้แค่ผลของ 02 ส่วน 07 ต้องใช้โมเดลจาก 05
ทุก notebook เพิ่ม `../scripts` เข้า path จึงต้องเปิด Jupyter จากโฟลเดอร์ `notebooks/`
(หรือโฟลเดอร์หลัก) ไม่ใช่จากที่อื่น

**4. Live demo ด้วยข้อมูลใหม่**

ใน `07_live_demo.ipynb` ตั้ง `FETCH_NOW = True` แล้วรันทุก cell โดย notebook จะ
1. เรียก `usgs_fetch.py` ดึงข้อมูลใหม่
2. เล่นเหตุการณ์ใหม่บนแผนที่ (`figures/step10_live_replay.html` เปิดในเบราว์เซอร์)
3. ให้คะแนนช่องตารางด้วย Isolation Forest ที่บันทึกไว้

ขั้นนี้จะเขียนทับไฟล์ raw และผล `step10_*` ตัวเลขจึงจะต่างจากชุดที่ล็อกไว้

**5. ผลลัพธ์อยู่ที่ไหน**

* ตัวเลขสุดท้ายทั้งหมดในหน้าเดียว: `results/step11_final_numbers.md`
* ข้อสรุป: `results/step9_conclusions.md`
* คำอธิบายทีละขั้นของ notebook 02-05: `docs/step3_*` ถึง `docs/step6_*`
* รายงาน (LaTeX, คอมไพล์ด้วย XeLaTeX): `report/report.tex`

## ค่าที่ใช้ร่วมกัน
ค่าที่ใช้ร่วมกันทุก step อยู่ใน `scripts/config.py` วิธีเรียกใช้ใน notebook:
```python
import sys; sys.path.append("../scripts")
from config import *
```

## โครงสร้างโฟลเดอร์
```
scripts/    usgs_fetch.py, config.py
data/raw/   quakes_m45_raw.csv = ข้อมูลย้อนหลัง + ข้อมูลสดในไฟล์เดียว (Step 1-2), backup/
data/processed/  quakes_sample.csv, quakes_clean.csv, cell_month_features.csv
notebooks/  01_download ... 07_live_demo (1 step = 1 notebook)
models/     โมเดลที่บันทึกไว้ (.joblib)     figures/  stepX_ชื่อรูป.png
results/    ตัวเลขทุกตัวที่ใช้ในสไลด์/รายงาน (.csv)
docs/       data_dictionary.md, stepX_*_explained.md     slides/ report/ video/
```

## กฎของทีม
- แก้เฉพาะไฟล์ของ step ที่ตัวเองรับผิดชอบ ถ้าจะแก้ของคนอื่นให้บอกกลุ่มก่อน
- ห้ามแบ่ง train/test แบบสุ่ม ให้แบ่งตามเวลาตาม `config.py`
- ตัวเลขทุกตัวในสไลด์/รายงานต้องมาจาก `results/*.csv`
- รูป: ภาษาอังกฤษ มีชื่อรูป มีชื่อแกนและหน่วย บันทึกที่ `FIG_DPI`
- ไฟล์ข้อมูล CSV อยู่ใน git (`data/raw/quakes_m45_raw.csv` ประมาณ 42 MB) ให้คนเดียวรัน `usgs_fetch.py` แล้ว push คนอื่น `git pull`

## คำสั่งดึงข้อมูล
```
python scripts/usgs_fetch.py              # Step 1-2: ดึงทุกอย่างที่ใหม่จนถึงตอนนี้ (รันก่อนใช้ข้อมูล)
python scripts/usgs_fetch.py --loop 300   # ไม่บังคับ: รันค้างไว้ อัปเดตทุก 5 นาที
python scripts/usgs_fetch.py --help       # ดูตัวเลือกทั้งหมด
```
