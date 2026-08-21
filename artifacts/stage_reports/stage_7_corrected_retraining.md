# Stage 7 — corrected TAP/POKE retraining and model v2

Date: 2026-08-21

Nine protocol-risk TAP/POKE trials were recollected under explicit duration and release rules. The corrected canonical manifest contains 315 unique, balanced Gold trials with no missing paths and finite 18x29 matrices. Superseded and REDO raw directories were removed only after replacement references passed validation.

On corrected data, the original whole-window three-policy comparison selected H/V/HV at Macro F1 0.8089. A pre-registered event-segmentation comparison then selected segmented/no-flip at Macro F1 0.8535 and balanced accuracy 0.8540.

Compared with model v1 (0.8316 Macro F1), v2 improves Macro F1 by 0.0219. TAP F1 improves from 0.7347 to 0.8817, POKE from 0.6598 to 0.7312, and direct TAP/POKE cross-confusions fall from 17 to 7. Fold Macro F1 values are 0.8745, 0.9061, and 0.7801. IMPACT/PAT performance is lower than v1 and fold variance is higher, so these remain documented tradeoffs.

The v2 package uses event segmentation, no spatial flip augmentation, StandardScaler + class-balanced RBF-SVM, C=10, gamma=scale, and all 315 corrected Gold trials. Package reload, schema, label, manifest, checksum, TAP prediction, POKE prediction, and 16 tests passed.

Model v1 remains a historical comparison. `scripts/recognize_live.py` now defaults to `models/deepskin_social_touch_v2`; live seven-class validation must be repeated before deployment acceptance.
