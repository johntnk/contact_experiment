# Stage 10: Positive-only conservative output gate

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Data: 315 audited Gold trials, three operators, seven target classes.
- Model: unchanged packaged v2 RBF-SVM; event-segmented 51-feature input.
- Gate: nearest same-class distance in the model's standardized feature space. Class thresholds use cross-operator positive-distance quantiles.
- Quantiles evaluated: 0.50, 0.70, 0.80, and 0.90.
- Initial configuration: 0.50, rejected by live testing as too strict.
- Selected configuration after operator feedback: 0.80.
- Leave-one-operator-out known-class metrics at 0.80: baseline accuracy 0.8603; output coverage 0.8698; selective precision 0.8832; correct target yield 0.7683; 41/315 known trials rejected; 32 incorrect predictions still accepted.
- Artifacts: `artifacts/experiments/positive_gate_v1/calibration_q50.json` through `calibration_q90.json`; `models/deepskin_social_touch_v2/positive_gate.joblib` and checksum.
- Verification: syntax checks and all 17 unit tests passed.
- Critical limitation: no unknown-class examples were used, so unknown rejection rate and false-trigger rate are not estimated. This is an experimental conservative gate, not proof of open-set safety.
- q0.80 live functional smoke: 9 GUI captures, 7 accepted target outputs and 2 `UNKNOWN` rejections. Every JSON had a same-stem raw NPZ and finite gate distance/threshold. Expected labels were unspecified, so no live accuracy or unknown-rejection metric is claimed. The operator reported the behavior as acceptable.
