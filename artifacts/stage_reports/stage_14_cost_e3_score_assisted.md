# Stage 14: E3 CoST source-score assisted target classifier

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `5b6356de871de1f0e36c3a52212f36818cdd2461`
- Source model: CoST-only RBF-SVM on 74 F0-common features, C=10, gamma=`scale`
- Target baseline: segmented Deepskin F1 event features
- Assisted representation: target F1 plus seven ordered CoST decision scores
- Evaluation: strict outer Leave-One-Deepskin-Operator-Out
- Target C/gamma selection: only the two outer-training operators

## Results

| Model | Macro F1 | Balanced accuracy | Accuracy |
|---|---:|---:|---:|
| Target-only F1 | 0.8535 | 0.8540 | 0.8540 |
| F1 + seven CoST scores | 0.8656 | 0.8667 | 0.8667 |
| Delta | +0.0121 | +0.0127 | +0.0127 |

Outer-operator Macro-F1 deltas were +0.0200, -0.0283, and +0.0474 for operator_01, operator_02, and operator_03. Two of three folds improved.

Per-class F1 deltas were IMPACT -0.0136, PAT -0.0307, POKE +0.0553, RUB +0.0383, STATIC_TOUCH -0.0019, STROKE +0.0138, and TAP +0.0235. No class exceeded the allowed -0.05 degradation.

Paired bootstrap across seeds 20260821/22/23 produced mean deltas near +0.012, probability of positive delta 0.801–0.819, and 95% intervals spanning approximately -0.016 to +0.040. The direction is favorable but uncertainty includes no gain.

## Source-score bias

The source model remains badly calibrated across sensors when interpreted as a standalone classifier. It predicts every Deepskin IMPACT, PAT, and STATIC_TOUCH trial as STATIC_TOUCH; it also predicts STATIC_TOUCH for 28/45 RUB and 33/45 STROKE trials, while 44/45 TAP trials become IMPACT. E3 does not expose these source predictions as outputs: the Deepskin-only target classifier learns how much information to take from the seven continuous scores.

## Gate decision

E3 passes the numerical transfer gates for fold count, pooled Macro F1, balanced accuracy, and maximum per-class degradation. The deterministic SVM produces identical fitted predictions across training seeds; the three fixed seeds apply to the paired bootstrap rather than adding model diversity. Bootstrap intervals include zero, so the improvement is not conclusive by itself.

E3 is retained as a model-selection candidate, not deployed. E4 and the complete candidate comparison/model-package provenance gate remain before any runtime replacement.

## Verification

- Smoke passed and its ignored output was permanently deleted.
- Full output contains exactly 315 predictions, 105/operator and 45/class.
- Source-score columns and reported metrics are finite.
- 20/20 unit tests passed.
- Artifacts: `artifacts/evaluation/cost_score_assisted_v1/metrics.json` and `predictions.csv`.
