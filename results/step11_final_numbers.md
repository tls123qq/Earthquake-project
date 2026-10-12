# Step 11: final numbers (results freeze)

Every number in the slides, report and video should come from this page.
Each line names the file it was copied from. After the freeze, no model is
retrained and no notebook is re-run with new data.

* **Data snapshot:** USGS M4.5+, 2000-01-01 to 2026-10-10 10:35:11 UTC
  (`results/step3_facts.csv`). The raw file may have newer rows after this, but
  they are not part of the results.
* **Reproducibility check (2026-10-12):** notebooks 02 to 07 were re-run top to
  bottom on a fresh copy of the repo. All six ran without error, and every
  results file came out identical except `step8_lgbm_tuning.csv`: the
  validation PR-AUC of six SMOTE settings that were not chosen moved by at most
  0.0005 (LightGBM is not bit-for-bit repeatable with SMOTE). The chosen
  settings and every metric in `classification_metrics.csv` stayed the same.
  Notebook 01 is not re-run because it downloads data.
* **Settings:** `scripts/config.py` (MIN_MAG 4.5, MAJOR_MAG 6.5, GRID_DEG 5,
  train ≤ 2019, validation 2020-2022, test 2023 onward, RANDOM_STATE 42).

## Step 3: preprocessing (`step3_summary.csv`, `step3_facts.csv`)

| Item | Value |
|---|---|
| Raw rows | 187,588 |
| Clean rows | 187,547 (41 removed) |
| Removed: magnitude below 4.5 | 4 |
| Removed: same event under two ids (≤ 10 s and ≤ 10 km) | 37 |
| Depth set to a default value (10, 30, 33, 35 km) | 87,087 rows (46.4%) |
| Major earthquakes (M ≥ 6.5) | 1,218 (0.65%) |
| Grid cells (5°) with events | 1,206 |

## Step 4: EDA (`eda_summary.csv`, `step4_mag_bands.csv`)

| Item | Value |
|---|---|
| Mean earthquakes per complete year (2000-2025) | 6,983 |
| Busiest year | 2011 (9,583) |
| Quietest complete year | 2001 (4,679) |
| Busiest month | 2011-03, 2,400 events, 82% in Japan |
| Share of events with M 4.5-5.0 | 74.4% |
| Completeness magnitude Mc | 4.7 |
| Gutenberg-Richter b-value | 1.14 (standard error 0.003) |
| Largest magnitude | 9.1 (Sumatra 2004, Tohoku 2011) |

## Step 5: clustering, ST-DBSCAN (`step5_facts.csv`, `step9_clustering_summary.csv`, `step5_known_events_check.csv`)

| Item | Value |
|---|---|
| Settings | eps1 = 100 km, eps2 = 7 days, min_samples = 5 |
| Clusters | 3,567 (1,991 aftershock sequences, 1,576 swarms) |
| Events labelled noise | 66.5% |
| Major earthquakes inside a cluster | 63.4% |
| Known events inside a cluster | 5 of 5, mean aftershock capture 0.94 |
| Largest clusters | Tohoku 2011 (2,980 events), Sumatra 2004 (2,326), Kamchatka 2025 (1,681) |

## Step 6: anomaly detection, Isolation Forest (`step6_facts.csv`, `anomaly_metrics.csv`)

The unit is a cell × week. A week counts as a true anomaly if it has an M ≥ 7.0
event. Contamination 0.002 was chosen on validation (best F1, set B).

| Test (2023 onward), 54 true anomalies in 13,548 cell-weeks | Precision | Recall | F1 | PR-AUC | Lift vs random |
|---|---|---|---|---|---|
| A: with max magnitude (leakage, shown only as a warning) | 0.759 | 0.407 | 0.530 | 0.601 | 190× |
| **B: without max magnitude (honest result, saved model)** | **0.424** | **0.259** | **0.322** | **0.274** | **106×** |
| C: activity only | 0.485 | 0.296 | 0.368 | 0.244 | 122× |

Random precision on test is 0.004.

## Steps 7-9: classification (`classification_metrics.csv`, `step8_tuned_threshold_comparison.csv`, `step9_bootstrap.csv`)

The unit is a cell × month. The target is "an M ≥ 6.5 occurs in this cell next
month". On test there are 134 positives in 54,180 rows (0.25%).

| Test, each model at the threshold tuned on validation | Threshold | Precision | Recall | F1 | PR-AUC |
|---|---|---|---|---|---|
| Naive baseline (major in last 12 months) | rule | 0.023 | 0.239 | 0.043 | 0.012 |
| Logistic Regression, no imbalance handling | 0.086 | 0.048 | 0.060 | 0.053 | 0.043 |
| **Logistic Regression, class weight (best)** | **0.972** | **0.055** | **0.142** | **0.079** | **0.041** |
| LightGBM, class weight (settings tuned on validation) | 0.952 | 0.054 | 0.090 | 0.067 | 0.035 |
| LightGBM, SMOTE (train only) | 0.544 | 0.043 | 0.119 | 0.063 | 0.029 |

* Logistic Regression at threshold 0.5 without imbalance handling: accuracy
  99.75%, but 0 of 134 majors found.
* Best model against the baseline (bootstrap): F1 +0.037 (95% CI +0.013 to
  +0.061), PR-AUC +0.029 (95% CI +0.010 to +0.052).
* Random PR-AUC on test is 0.0025, so the best model is about 16× random. It
  still raises 326 false alarms out of 345 and misses 115 of 134 majors.
* Features with a clear effect: `n_major_12m`, `nbr_major_12m`.

## Step 10: live demo (`step10_live_summary.csv`, `step10_live_anomaly.csv`)

| Item | Value |
|---|---|
| Live window | 2026-10-08 10:00 to 2026-10-10 10:35 UTC (48.5 hours) |
| New events (M4.5+) | 69 (34.2 per day) in 24 cells |
| Largest new event | M7.7, Panama |
| Isolation Forest on that cell-week | score 0.677, below the cut 0.683, so not flagged (the week was not complete yet) |

## Things to say the same way everywhere

* Two different targets: the anomaly step uses M ≥ 7.0 per cell-week, the
  classification step uses M ≥ 6.5 next month per cell. That is why the
  positive counts differ (54 vs 134).
* Grid cells: 1,206 in Steps 3-6, 1,204 in Step 7 because 2 cells at longitude
  180 were merged with −180 (`step7_table_summary.csv`).
* Neither model predicts earthquakes. Both rank cells by risk better than random.
