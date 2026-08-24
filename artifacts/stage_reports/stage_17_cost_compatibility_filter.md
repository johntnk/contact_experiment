# Stage 17: CoST capture-level compatibility filter

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `5b6356de871de1f0e36c3a52212f36818cdd2461`
- Metric version: `cost-compatibility-v1`
- Filter version: `cost-compatibility-filter-v1`
- Config SHA-256: `66589c30d657eebeeb1d29db212148606e1f8693d998d97bf0523398929ef757`

## Frozen rules

- TAP: exactly one detected pressure pulse.
- PAT: at least two pulses and contact-area ratio at least 0.3125, the CoST TAP median.
- STROKE: one continuous contact, no complete release, reversal count at most 5 (CoST stroke median), and straightness at least 0.0614715 (CoST stroke p25).
- RUB: one continuous contact, no complete release, and at least 3 effective direction changes. A count of 1 is treated as the smoothing-edge baseline rather than a clear reversal.
- HIT, SLAP, POKE, and PRESS: retained after explicit mapping; no additional rule was justified by the frozen definitions.

No Deepskin outer-test result was used to set or change these thresholds.

## Counts

| Label | Before | Kept | Filtered |
|---|---:|---:|---:|
| IMPACT | 1116 | 1116 | 0 |
| PAT | 557 | 262 | 295 |
| POKE | 558 | 558 | 0 |
| RUB | 557 | 430 | 127 |
| STATIC_TOUCH | 558 | 558 | 0 |
| STROKE | 556 | 211 | 345 |
| TAP | 558 | 292 | 266 |
| Total | 4460 | 3427 | 1033 |

## Artifacts

- `artifacts/cost/cost_compatibility_metrics.csv`
- `artifacts/cost/cost_compatibility_summary.json`
- `artifacts/cost/cost_filter_config.yaml`
- `artifacts/cost/cost_filter_decisions.csv`
- `artifacts/cost/cost_filter_report.json`
- `artifacts/cost/cost_filter_counts.csv`
- `artifacts/features/cost_f0_common_filtered.csv`

## Verification

- Metric extraction smoke and filter-application smoke passed before formal outputs.
- Smoke artifacts were deleted after validation.
- Formal metrics and original F0 rows joined one-to-one for all 4,460 captures.
- 22/22 unit tests passed.

Next: rerun E1–E4 into non-overwriting v2 directories using only the 3,427 retained rows and record the filter config hash in every experiment.
