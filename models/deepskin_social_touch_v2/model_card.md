# Deepskin social-touch model v2.0.0

Seven-class target-only RBF-SVM trained on all 315 audited real Gold trials. Policy: none; event segmentation: True; fitted rows: 315. Fixed configuration: C=10.0, gamma=scale, selected by nested Leave-One-Operator-Out validation.

Cross-validated performance on untouched original trials: Macro F1 0.8535, balanced accuracy 0.8540. These are cross-validation estimates, not training-set scores.

Classes: IMPACT, PAT, POKE, RUB, STATIC_TOUCH, STROKE, TAP.

Limitations: only three operators; all real data were collected with the left hand; results do not establish right-hand generalization. Input must use the exact 51-feature extractor, event-segmentation setting, and 18x29 matrix orientation recorded in this package.
