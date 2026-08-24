# Stage 16: E0–E4 transfer audit and provisional model decision

- Date: 2026-08-21
- Audited outputs: E1 source-only, E2 weighted joint, E3 score-assisted, E4 source-informed selection, and matched E0 baselines
- Prediction completeness: 315 pooled out-of-fold target rows per evaluated configuration
- Primary metric: seven-class Macro F1

## Outcome

E3 is the performance winner at Macro F1 0.8656 versus the matched E0/F1 value 0.8535. It passes the numerical fold, mean-gain, balanced-accuracy, and per-class gates. E2 and E4 are rejected; E1 remains diagnostic.

The audit does not authorize deployment because capture-level CoST compatibility filtering and its config hash are missing. E3 is frozen only as a provisional performance candidate. The existing target-only runtime model remains unchanged.

Generated formal artifacts:

- `artifacts/evaluation/cost_transfer_results.csv`
- `artifacts/evaluation/cost_domain_shift_report.md`
- `artifacts/evaluation/cost_transfer_decision.md`

Next gate: implement the missing source compatibility filter, rebuild source artifacts, and rerun transfer experiments without changing rules based on outer-test results.
