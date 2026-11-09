# Stage 3 Gold Collection Progress

- Updated: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Raw data tracked by Git: no
- GPU used: no

## Completed sessions

| Operator | Session | Gold | Attempts | REDO | Class balance | Gate |
|---|---:|---:|---:|---:|---|---|
| operator_01 | session_01 | 35 | corrected | superseded removed | 7 classes x 5 | passed |
| operator_01 | session_02 | 35 | corrected | superseded removed | 7 classes x 5 | passed |
| operator_01 | session_03 | 35 | corrected | superseded removed | 7 classes x 5 | passed |
| operator_02 | session_01 | 35 | 44 | 0 | 7 classes x 5 | passed |
| operator_02 | session_02 | 35 | 36 | 1 | 7 classes x 5 | passed |
| operator_02 | session_03 | 35 | 35 | 0 | 7 classes x 5 | passed |
| operator_03 | session_01 | 35 | 35 | 0 | 7 classes x 5 | passed |

## Data audit

- Planned trial IDs are contiguous and unique from 1 through 35 within each completed session.
- Every valid trial has matching instruction and verified labels.
- Every matrix is finite and shaped `[T,18,29]`.
- The pulse_count correction plan has 39/39 corrected replacements; all superseded raw attempts were removed after the final gate.
- Accepted trials across the six completed sessions contain 735–750 host polls over approximately four seconds.
- Host-observed matrix update rate across the six sessions is 52.70–53.21 Hz (mean 52.94 Hz).
- The SDK touch flag is always false and remains explicitly quality-flagged.
- The current Gold manifest contains exactly 245 eligible rows.

## Overall progress

```text
operator_01: 105 / 105
operator_02: 105 / 105
operator_03: 35 / 105
total:      245 / 315
```

Pulse correction is complete. Normal collection can resume with
The next collection is `operator_03/session_02` after a session break and a new
device initialization.
