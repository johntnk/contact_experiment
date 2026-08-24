# Stage 15: E4 CoST-informed shared feature selection

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `5b6356de871de1f0e36c3a52212f36818cdd2461`
- Source ranking: CoST subject-grouped 5-fold permutation importance, three repeats
- Candidate subset sizes: 16, 32, 48, and all 74 F0-common features
- Seeds: 20260821, 20260822, 20260823
- Target model: RBF-SVM trained only on Deepskin outer-training operators
- Target subset and C/gamma selection: only the two outer-training operators

## Results

| Seed | Full-F0 Macro F1 | Selected Macro F1 | Delta | Selected sizes by outer fold |
|---:|---:|---:|---:|---|
| 20260821 | 0.8390 | 0.8253 | -0.0137 | 32 / 74 / 74 |
| 20260822 | 0.8390 | 0.8161 | -0.0230 | 32 / 74 / 74 |
| 20260823 | 0.8390 | 0.8224 | -0.0167 | 48 / 74 / 74 |

For operator_02 and operator_03, inner validation rejected feature reduction and retained all 74 features, producing exactly the baseline result. For operator_01, inner validation selected 32 or 48 CoST-ranked features, but outer Macro F1 fell by -0.0353, -0.0707, and -0.0502 across seeds.

The highest-ranked source features were reasonably stable and emphasized temporal derivative, duration, normalized centroid movement, trajectory straightness, total-pressure maximum, and several pooled spatial regions. This source-domain stability did not transfer into a useful Deepskin subset.

## Gate audit

- Macro F1 decreased for every seed.
- Balanced accuracy decreased by -0.0127 to -0.0222.
- Some seeds exceeded the maximum permitted per-class degradation, including STATIC_TOUCH -0.0601 and POKE -0.0505.
- Bootstrap probability of positive benefit was only 0.012–0.089; two seed intervals were entirely negative.
- Prediction output contains 945 rows, exactly 315 per seed.

E4 fails the transfer gate and is not a model candidate. This is retained as a negative result showing that CoST feature rankings should not be used to prune the current sensor's F0 representation.

## Verification

- Smoke passed before the full experiment and its ignored output was deleted.
- 20/20 unit tests passed.
- Artifacts: `artifacts/evaluation/cost_feature_selected_v1/metrics.json` and `predictions.csv`.

Next: perform the complete E0/E1/E2/E3/E4 candidate audit. E3 remains the only CoST-assisted candidate; no runtime model changes have been made.
