# Stage 2 Data Schema and Recorder Report

- Date: 2026-08-20
- Branch: `stage-2-recorder`
- Starting commit: `b487f0b6fa460c7f39ef3fd03a1835676cfc0c52`
- Schema: `deepskin-trial-v1`
- Session-order smoke seed: `20260820`
- GPU used: no
- Result: passed

## Implemented

- Strict seven-label metadata validation and explicit `VALID`, `REDO`, or
  `UNCERTAIN` confirmation.
- Atomic raw trial publication with refusal to overwrite existing trials.
- `matrix.npz`, `metadata.json`, and `sdk_events.jsonl` recording.
- Host-monotonic timestamps, contiguous host frame IDs, changed-matrix update
  rate, separate host poll rate, and SDK touch-state preservation.
- Read-only trial replay/validation and Gold-only manifest construction.
- Deterministic 35-trial session orders with five trials per class and no run of
  more than two identical labels.
- Nine versioned session orders covering three operators and three sessions,
  totaling 315 planned trials.

## Validation

- 10 unit tests passed.
- All nine session orders contain 35 rows; total planned rows: 315.
- Hardware acceptance `trial_000006`:
  - matrix shape: `[553,18,29]`
  - duration: 2984 ms
  - changed transitions: 156
  - host-observed matrix update rate: 52.61 Hz
  - host poll rate: 185.32 Hz
  - explicit label: `VALID / TAP / CONTROLLED_CONFIRMED / GOLD`
- Final acceptance manifest contains exactly the corrected `trial_000006`.
- Earlier acceptance attempts were preserved as REDO/UNCERTAIN or legacy-metric
  audit records and excluded from the final manifest.

Acceptance data is under ignored `data/interim/stage2_acceptance_v1` and is not
intended for source control or the 315-trial Gold corpus.

## Known limitation

`deepskin_is_touching()` stayed false during accepted touches. The raw field is
preserved and the manifest adds `SDK_TOUCH_FLAG_ALWAYS_FALSE`; downstream event
segmentation must use matrix-relative signal evidence rather than this flag alone.

## Gate result

Passed. A single trial can be recorded, explicitly confirmed, atomically saved,
replayed, validated, and included or excluded from the Gold manifest correctly.
