# Final CoST transfer decision after compatibility filtering

Date: 2026-08-21

## Frozen source preparation

- Filter version: `cost-compatibility-filter-v1`
- Filter config SHA-256: `66589c30d657eebeeb1d29db212148606e1f8693d998d97bf0523398929ef757`
- Mapped source captures: 4,460
- Retained compatible captures: 3,427
- Filtered ambiguous captures: 1,033

Every v2 E1–E4 metrics file records the same filter version and hash.

## Results

| Experiment | Result | Decision |
|---|---|---|
| E0 target-only F1 | Macro F1 0.8535 | Selected |
| E1 source-only | CoST internal 0.7422; Deepskin 0.1172 | Diagnostic only |
| E2 weighted joint RBF-SVM | 0.8274 versus matched F0 baseline 0.8321 | Rejected |
| E3 source-score assisted | 0.8533 versus matched F1 baseline 0.8535 | Rejected: no mean gain |
| E4 source-informed subset | 0.8000–0.8221 versus 0.8390 | Rejected |

E3 outer-fold deltas were +0.0115, -0.0385, and +0.0302. Although two folds improved, pooled Macro F1 changed by -0.00025 rather than the required +0.01. Balanced accuracy was unchanged. Bootstrap probability of positive gain was 0.493–0.505 with confidence intervals centered around zero. E3 therefore does not pass the mean-gain gate.

## Final selection

The frozen final training recipe is:

```text
training_recipe = target_only
model_family = RBF-SVM
feature_space = segmented Deepskin F1
augmentation = none
```

The existing Deepskin-only v2 runtime model remains the correct release candidate. CoST is retained for source-domain reproduction, domain-shift analysis, and negative/neutral transfer evidence, but no CoST samples, scores, or selected feature subsets enter the final classifier.

The filtered experiments do not support the earlier unfiltered E3 provisional gain. The unfiltered v1 artifacts remain available only for audit history and must not be used for model selection.

## Next action

Build and audit the final target-only model package using all 315 Gold events. Do not claim a new test score from the full-data fit; the release performance claim remains the strict outer pooled Macro F1 0.8535.
