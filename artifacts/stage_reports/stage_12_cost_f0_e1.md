# Stage 12: CoST F0 common features and E1 source-only diagnostic

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `5b6356de871de1f0e36c3a52212f36818cdd2461`
- Feature schema: `f0-common-v1`, 74 features, including normalized temporal summaries and fixed 4×4 spatial pooling
- Model: RBF-SVM, C=10, gamma=`scale`, balanced class weights
- Source data: 4,460 mapped CoST captures from 31 subjects
- Target audit data: 315 Deepskin Gold trials, 45 per class and 105 per operator

## Commands

```powershell
python scripts/extract_cost_features.py
python scripts/run_cost_source_only.py --smoke
python scripts/run_cost_source_only.py
python -m unittest discover -s tests -v
```

The ignored smoke output was deleted after the pipeline passed. CoST matrices were processed at their native 135 Hz using real timestamps; they were not interpolated to the Deepskin sampling rate.

## Results

| Evaluation | Rows | Macro F1 | Balanced accuracy | Accuracy |
|---|---:|---:|---:|---:|
| CoST subject-grouped 5-fold CV | 4,460 | 0.6587 | 0.6622 | 0.6742 |
| CoST-only model on Deepskin Gold | 315 | 0.1036 | 0.1746 | 0.1746 |
| Deepskin operator_01 | 105 | 0.1278 | 0.1905 | 0.1905 |
| Deepskin operator_02 | 105 | 0.0980 | 0.1714 | 0.1714 |
| Deepskin operator_03 | 105 | 0.0834 | 0.1619 | 0.1619 |

The cross-domain model predicted `STATIC_TOUCH` for 209/315 target trials. This collapse occurs for all three operators, supporting a strong sensor/domain-shift diagnosis rather than an operator-specific anomaly.

## Audit and decision

- Source CV is grouped by CoST subject; no source subject crosses its validation fold.
- E1 training uses CoST only, while the 315 Deepskin trials are test-only.
- Prediction rows, class balance, operator balance, confusion matrices, and finite metrics were verified.
- The existing Deepskin-only LOPO baseline (Macro F1 0.8535) remains the valid runtime candidate.
- E1 is diagnostic only and is not eligible for runtime model selection.
- The smallest next experiment is E2: add CoST to each outer Deepskin training fold at conservative source weights, while keeping the held-out Deepskin operator strictly untouched.

## Artifacts

- `artifacts/features/cost_f0_common.csv`
- `artifacts/features/cost_f0_coverage.json`
- `artifacts/evaluation/cost_source_only_v1/metrics.json`
- `artifacts/evaluation/cost_source_only_v1/deepskin_predictions.csv`

Verification: 19/19 unit tests passed.
