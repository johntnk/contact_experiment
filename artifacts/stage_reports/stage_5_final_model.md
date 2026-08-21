# Stage 5 — final model package

Date: 2026-08-21

The selected horizontal+vertical augmentation policy was fitted on all 315 audited real Gold trials. Original, horizontal, vertical, and both-axis transforms produced 1260 fitted feature rows. The packaged classifier is a standardized, class-balanced RBF-SVM with C=10 and gamma=0.01, the modal configuration selected by the nested Leave-One-Operator-Out experiment.

The model package is `models/deepskin_social_touch_v1/` and contains the serialized model, 315-row training manifest, 51-feature schema, seven-class label map, frozen training configuration, model card, and SHA-256 checksums.

Delivery audit:

- model reload succeeded;
- scaler input count and feature schema both equal 51;
- model classes exactly match the seven label-map values;
- training manifest has 315 unique trial keys;
- configuration records 315 real trials and 1260 augmented fit rows;
- all six package payload checksums match;
- end-to-end prediction of `operator_03/session_03/trial_000035` returned `STROKE`, matching its Gold label;
- all 15 unit tests passed.

The published performance estimate remains the untouched-original nested LOPO result: Macro F1 0.8316 and balanced accuracy 0.8286. No training-set score is presented as a generalization estimate. The package is left-hand-only in terms of real data and has not been validated on real right-hand trials.
