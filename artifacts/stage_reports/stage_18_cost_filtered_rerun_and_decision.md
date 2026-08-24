# Stage 18: Filtered E1–E4 rerun and final transfer decision

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `5b6356de871de1f0e36c3a52212f36818cdd2461`
- Source rows: 3,427 filtered CoST captures
- Filter SHA-256: `66589c30d657eebeeb1d29db212148606e1f8693d998d97bf0523398929ef757`

## Execution and audit

- All four filtered pipeline smokes passed before formal execution.
- Smoke directories were permanently deleted after verification.
- E1–E4 wrote new v2 directories and did not overwrite v1 history.
- Prediction counts: E1 315, E2 2,835, E3 315, E4 945.
- Every v2 metrics file contains the same filter version and config hash.
- All metrics and score columns were finite.
- 22/22 unit tests passed.

## Decision

Filtering improved CoST internal Macro F1 to 0.7422, but cross-domain E1 remained 0.1172. E2 and E4 failed. E3 became neutral: 0.8533 versus target-only 0.8535, with bootstrap probability near 0.5. No filtered CoST transfer method passes the frozen gate.

Final selection: `training_recipe = target_only`. The runtime model has not been changed during this rerun. Next step is final target-only package construction and reproducibility audit using all 315 Gold events.

Authoritative artifacts:

- `artifacts/evaluation/cost_transfer_results_v2.csv`
- `artifacts/evaluation/cost_transfer_decision_v2.md`
- `artifacts/evaluation/cost_domain_shift_report.md`
