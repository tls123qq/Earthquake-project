# Step 9 conclusions

## Classification (Steps 7-8)

1. Accuracy is misleading: Logistic Regression without imbalance handling scores 99.8% accuracy but catches 0 of 134 majors (F1 = 0).
2. Best model: 2_logreg_class_weight with a threshold tuned on validation (0.972). On test: precision 0.055, recall 0.142, F1 0.079, PR-AUC 0.041.
3. It beats the naive baseline (F1 0.043, PR-AUC 0.012): F1 +0.037 (95% CI +0.013 to +0.061), PR-AUC +0.029 (95% CI +0.010 to +0.052); the baseline wins in 0.05% of resamples.
4. PR-AUC 0.041 is 16x a random guess (0.0025), but 326 of 345 alarms are false and 115 of 134 majors are missed: useful for ranking risky cells, not as a warning system.
5. Feature importance is noisy (only 102 validation positives); the features with a clear effect are n_major_12m, nbr_major_12m, i.e. recent major activity in the cell and its neighbours. Class weighting helped Logistic Regression more than LightGBM; SMOTE did not help. LightGBM was not tuned, so this comparison is indicative only.

## Anomaly detection (Step 6)

1. Honest result (set B, without max magnitude), test: precision 0.424, recall 0.259, F1 0.322, PR-AUC 0.274, 106x better precision than random (0.004).
2. With max magnitude (set A) the test scores rise to precision 0.759, recall 0.407, PR-AUC 0.601. That gap is the leakage effect: the feature is computed from the same values as the answer.

## Clustering (Step 5)

1. Chosen ST-DBSCAN settings: eps1 = 100 km, eps2 = 7 days, min_samples = 5; 3,567 clusters, 66.5% of events are noise.
2. Checked against real events: 5 of 5 known events fall inside a cluster (mean aftershock capture 0.94); the 3 largest clusters are Japan M9.1 2011-03-11, 2004 Sumatra - Andaman Islands Earthquake M9.1 2004-12-26 and Russia M8.8 2025-07-29.
