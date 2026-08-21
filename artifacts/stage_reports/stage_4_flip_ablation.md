# Stage 4 — flip augmentation ablation

Date: 2026-08-21

## Experiment contract

- Data: 315 real Deepskin Gold trials, 3 operators, 3 sessions/operator, 7 classes x 45 trials.
- Model: standardized RBF-SVM with class balancing.
- Evaluation: nested Leave-One-Operator-Out; each outer fold tests 105 untouched real trials.
- Model selection: inner operator-held-out Macro F1 over `C={0.1,1,10,100}` and `gamma={scale,0.01,0.1,1}`.
- Augmentation is applied only to training folds. Validation and outer test folds use original matrices only.
- Policies: `none` (1x), `horizontal` (2x), `horizontal_vertical` (4x: original, H, V, HV).
- Feature family: 51 pressure, active-area, temporal, normalized-centroid, movement, and direction summary features.
- Runtime: Python 3.12, scikit-learn 1.9.0, scipy 1.18.0. RBF-SVM ran on CPU; GPU was not used.

## Results

| Policy | Pooled Macro F1 | Balanced accuracy | Accuracy | Fold Macro F1 mean ± population SD |
|---|---:|---:|---:|---:|
| none | 0.7988 | 0.7968 | 0.7968 | 0.8005 ± 0.0132 |
| horizontal | 0.7810 | 0.7810 | 0.7810 | 0.7823 ± 0.0282 |
| horizontal_vertical | **0.8316** | **0.8286** | **0.8286** | **0.8326 ± 0.0404** |

Outer-fold Macro F1:

| Policy | operator_01 | operator_02 | operator_03 |
|---|---:|---:|---:|
| none | 0.7971 | 0.8181 | 0.7863 |
| horizontal | 0.7926 | 0.8105 | 0.7438 |
| horizontal_vertical | **0.8395** | **0.8782** | 0.7800 |

Per-class F1 for the best candidate (`horizontal_vertical`): IMPACT 0.9195, PAT 0.9451, POKE 0.6598, RUB 0.8434, STATIC_TOUCH 0.8936, STROKE 0.8250, TAP 0.7347.

## Audit

- All policies evaluated exactly 315 unique `(operator, session, planned_trial)` keys, and the key sets are identical.
- Training/test operator overlap is rejected at runtime.
- Training rows per outer fold are 210, 420, and 840 for the 1x, 2x, and 4x policies; test rows remain 105 for every policy/fold.
- Fifteen unit tests passed before the full run.
- Metrics, predictions, feature schemas, and three fold models per policy are stored under `artifacts/experiments/flip_ablation_full_v1/`.

## Conclusion and limitation

The 4x horizontal+vertical policy is the current candidate: pooled Macro F1 improves by 0.0327 over no augmentation. Horizontal-only augmentation is rejected because it lowers pooled and mean fold performance. The best policy is not uniformly better: operator_03 drops from 0.7863 to 0.7800, and only three operators are available. These experiments do not establish right-hand generalization because all real trials were left-hand trials; mirrored matrices are synthetic spatial transformations, not real right-hand biomechanics.
