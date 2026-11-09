# Deepskin social-touch model v1.0.0

Seven-class target-only RBF-SVM trained on all 315 audited real Gold trials, with original/horizontal/vertical/both training transforms (1260 fitted rows). The fixed configuration is C=10 and gamma=0.01, selected as the modal nested Leave-One-Operator-Out configuration of the best augmentation policy.

Cross-validated performance on untouched original trials: Macro F1 0.8316, balanced accuracy 0.8286. These are cross-validation estimates, not training-set scores.

Classes: IMPACT, PAT, POKE, RUB, STATIC_TOUCH, STROKE, TAP.

Limitations: only three operators; all real data were collected with the left hand; matrix mirroring does not establish right-hand generalization; POKE and TAP remain the weakest classes. Input must use the exact 51-feature extractor and 18x29 matrix orientation recorded in this package.
