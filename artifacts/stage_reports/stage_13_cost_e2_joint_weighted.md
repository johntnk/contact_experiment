# Stage 13: E2 class/domain-balanced CoST joint training

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `5b6356de871de1f0e36c3a52212f36818cdd2461`
- Feature schema: `f0-common-v1`, 74 features
- Outer evaluation: Leave-One-Deepskin-Operator-Out, 315 pooled out-of-fold predictions per configuration
- Inner selection: the two outer-training operators select alpha; the outer-test operator is never used
- Source weights: class-balanced within CoST, with source/target total-weight ratio alpha
- Alpha candidates: 0.05, 0.10, 0.25, 0.50, 1.00
- Seeds: 20260821, 20260822, 20260823

## Models

- RBF-SVM: C=10, gamma=`scale`
- Extra Trees: 300 trees, minimum leaf size 2
- Random Forest: 300 trees, minimum leaf size 2, sqrt feature sampling

## Pooled results

| Family | Seed | Target-only Macro F1 | Joint Macro F1 | Delta |
|---|---:|---:|---:|---:|
| RBF-SVM | all three | 0.8321 | 0.8468 | +0.0146 |
| Extra Trees | 20260821 | 0.8280 | 0.8404 | +0.0124 |
| Extra Trees | 20260822 | 0.8343 | 0.8245 | -0.0098 |
| Extra Trees | 20260823 | 0.8437 | 0.8366 | -0.0071 |
| Random Forest | 20260821 | 0.8120 | 0.8145 | +0.0025 |
| Random Forest | 20260822 | 0.8050 | 0.8069 | +0.0020 |
| Random Forest | 20260823 | 0.8052 | 0.8040 | -0.0011 |

RBF-SVM selected alpha 0.05 in every outer fold and seed. Its balanced-accuracy delta was +0.0159. Per-class F1 deltas were IMPACT +0.0209, PAT +0.0486, POKE +0.0047, RUB -0.0432, STATIC_TOUCH -0.0026, STROKE +0.0620, and TAP +0.0119.

## Gate audit

RBF-SVM was the only configuration with a stable positive pooled delta across all three seeds. Its paired bootstrap mean delta was about +0.015, probability of positive delta was 0.816–0.825, and the 95% intervals included zero.

It does **not** pass the frozen release gate. Its outer-fold Macro-F1 deltas were -0.0254, -0.0023, and +0.0655, so only one of three folds was non-decreasing; the requirement is at least two. Extra Trees and Random Forest were not directionally consistent across seeds.

Decision: retain E2 as a completed transfer experiment, but do not replace or retrain the current runtime model from it. Proceed to E3 source-score assistance, which uses CoST scores as auxiliary features while fitting the final classifier only with Deepskin labels.

## Verification

- Smoke passed before the full run; its ignored temporary directory was deleted.
- 20/20 unit tests passed.
- Full prediction table contains 2,835 rows: 315 for each of nine family/seed configurations.
- All result metrics are finite and every configuration contains all three outer operators.
- Artifacts: `artifacts/evaluation/cost_joint_weighted_v1/metrics.json` and `predictions.csv`.
