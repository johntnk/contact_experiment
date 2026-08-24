# CoST mapping report

Mapping version: `cost-to-deepskin-v1`

| CoST label | Target label | Captures |
|---|---:|---:|
| grab | discard | 558 |
| hit | IMPACT | 558 |
| massage | discard | 557 |
| pat | PAT | 557 |
| pinch | discard | 558 |
| poke | POKE | 558 |
| press | STATIC_TOUCH | 558 |
| rub | RUB | 557 |
| scratch | discard | 558 |
| slap | IMPACT | 558 |
| squeeze | discard | 557 |
| stroke | STROKE | 556 |
| tap | TAP | 558 |
| tickle | discard | 557 |

Kept captures: 4460 / 7805.
Ambiguous labels were not inferred; only the frozen explicit mapping was retained.

## Capture-level compatibility filter

- Filter version: `cost-compatibility-filter-v1`
- Config SHA-256: `66589c30d657eebeeb1d29db212148606e1f8693d998d97bf0523398929ef757`
- Input mapped captures: 4,460
- Retained compatible captures: 3,427
- `FILTERED_AMBIGUOUS`: 1,033
- Thresholds were frozen from CoST-only distributions and the written action definitions before rerunning transfer experiments.

Retained counts: IMPACT 1116, PAT 262, POKE 558, RUB 430, STATIC_TOUCH 558, STROKE 211, TAP 292.
