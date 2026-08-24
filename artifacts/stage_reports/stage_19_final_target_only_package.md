# Stage 19: Final target-only model package

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `5b6356de871de1f0e36c3a52212f36818cdd2461`
- Package: `models/deepskin_social_touch_v3_target_only`
- Model version: `3.0.0`
- Training recipe: `target_only`

## Frozen configuration

- 315 audited Gold trials: 3 operators × 3 sessions × 7 classes × 5 trials
- Event segmentation enabled
- No flip augmentation
- 51 Deepskin F1 event features
- RBF-SVM, C=10, gamma=`scale`, balanced class weights

The full-data fit is not treated as a new test result. The release performance claim remains the strict outer Leave-One-Operator-Out pooled Macro F1 0.8535 and balanced accuracy 0.8540.

## Package audit

- All seven labels have exactly 45 training trials.
- Each operator has 105 trials; each of nine operator/session pairs has 35.
- The serialized pipeline contains the expected seven classes and 51-feature schema.
- Pipeline predictions equal the independent scaler + classifier prediction path.
- Repeated warm single-row classifier prediction averaged approximately 0.197 ms on this host; this excludes SDK acquisition, event segmentation, feature extraction, and GUI overhead.
- A real Gold trial (`operator_01/session_01/trial_000001_attempt_03`) replayed successfully as RUB, matching its verified label.
- All package checksums passed.
- 22/22 unit tests passed.

## Compatibility with current runtime

The new `model.joblib` SHA-256 is `eb6c1ad44c1ad50ee9b9984e550b3724af3522a1f9e508f0d3f2ce70b86a6d4d`, exactly equal to the current v2 classifier. Therefore the current runtime already uses the frozen final classifier, and its q0.80 positive gate remains model-compatible. No runtime path was switched in this stage.

## Package contents

- model and independent preprocessing objects
- feature schema and frozen label map
- model card and training/config records
- complete 315-row training manifest
- outer-CV metrics and confusion matrix
- CoST provenance plus explicit zero-row source-training manifest
- SHA-256 checksum manifests

Next: runtime/output protocol audit and final delivery documentation. Do not recalibrate or deploy a different classifier unless a new evaluation gate is completed.
