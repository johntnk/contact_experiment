# Experiment Ledger

## Stage 10 positive-only conservative gate — q0.80 selected

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: v2 classifier plus class-conditional nearest-positive gate; initial q0.50 was too strict in live use, selected cross-operator quantile 0.80
- Seed: not applicable; deterministic LOPO evaluation
- GPU: not used
- Command: `python scripts/calibrate_positive_gate.py` at quantiles 0.50, 0.70, 0.80, and 0.90; 17-test unit suite
- Artifacts: `artifacts/experiments/positive_gate_v1/`, `models/deepskin_social_touch_v2/positive_gate.joblib`, and `artifacts/stage_reports/stage_10_positive_only_gate.md`
- Known-class metrics at q0.80: coverage 0.8698; selective precision 0.8832; correct target yield 0.7683; baseline accuracy 0.8603
- Status: q0.80 packaged after user feedback that q0.50 rejected too many target actions; GUI restart required; unknown rejection remains unmeasured
- Live functional smoke: 9 captures at q0.80; 7 accepted and 2 rejected as `UNKNOWN`; all raw NPZ files present. Expected labels were unspecified, so this validates plumbing only, not accuracy. Operator feedback: acceptable.

## Stage 9 runtime orientation canonicalization — smoke passed

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: packaged v2 model; event segmentation; runtime orientation `normal` or `rotate_180`
- Seed: not applicable; deterministic matrix transform
- GPU: not used
- Commands: Python syntax compilation, 16-test unit suite, and live CLI `--help` smoke
- Artifact: `artifacts/stage_reports/stage_9_orientation_canonicalization.md`
- Metrics: 16/16 tests passed; no hardware accuracy metric claimed yet
- Status: software smoke passed; paired normal/180-degree live validation is next

## Stage 2 recorder smoke — passed

- Branch: `stage-2-recorder`
- Starting commit: `b487f0b6fa460c7f39ef3fd03a1835676cfc0c52`
- Config: `deepskin-trial-v1`, seven V1 labels, host monotonic timestamps
- Seed: `20260820` for session-order smoke
- GPU: not used
- Commands: `python -m unittest discover -s tests -v`, session-order generator,
  `record_trial.py`, `replay_trial.py`, and `build_gold_manifest.py`
- Artifact paths: ignored `data/interim/stage2_acceptance_v1`, versioned
  `artifacts/stage_reports/stage_2_recorder.md`, and nine files under
  `protocol/session_orders/`
- Metrics: 10 tests passed; final trial `[553,18,29]`; observed updates 52.61 Hz;
  host polls 185.32 Hz; final acceptance manifest 1 eligible trial
- Status: smoke and single hardware-trial gate passed; 315-trial collection not started

## Stage 3 session runner smoke — passed

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: `operator_01/session_01`, simulated SDK, one new trial limit
- Seed/order: versioned `operator_01_session_01.csv` (seed 20260821)
- GPU: not used
- Commands: `record_session.py --simulate --max-new-trials 1`, replay, manifest
- Artifact path: temporary `data/interim/stage3_runner_smoke_v1` (deleted after validation)
- Metrics: 12 tests passed; one simulated trial recorded/replayed; one eligible manifest row
- Status: session-runner smoke passed; formal Gold collection not started

## Stage 3 Gold collection — operator_01/session_01 block 1

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_01.csv` (seed 20260821)
- GPU: not used
- Artifact paths: ignored `data/raw/deepskin/operator_01/session_01` and
  `data/processed/manifests/gold_manifest.csv`
- Attempts: 6 total; 5 VALID Gold; 1 REDO
- Labels accepted: RUB, POKE, TAP, IMPACT, STROKE
- Observed matrix update rate: 52.71–52.96 Hz
- Frames per accepted trial: 743–748; all matrices finite and shaped `[T,18,29]`
- Quality flag: SDK touch state false in every frame; matrix signal remained nonzero
- Status: block passed; session progress 5/35 Gold, overall progress 5/315 Gold

## Stage 3 Gold collection — operator_01/session_01 block 2

- Branch: `stage-3-gold-collection`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_01.csv` (seed 20260821)
- GPU: not used
- Artifact paths: ignored raw session directory and current canonical Gold manifest
- Attempts cumulative: 11 total; 10 VALID Gold; 1 REDO
- Labels cumulative: TAP 3, POKE 2, STROKE 2, RUB 1, PAT 1, IMPACT 1
- Observed matrix update rate: 52.71–53.21 Hz
- Frames per accepted trial: 743–748; all matrices finite and shaped `[T,18,29]`
- Status: block passed; session progress 10/35 Gold, overall progress 10/315 Gold

## Stage 3 Gold collection — operator_01/session_01 block 3

- Branch: `stage-3-gold-collection`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_01.csv` (seed 20260821)
- GPU: not used
- Attempts cumulative: 16 total; 15 VALID Gold; 1 REDO
- Labels cumulative: TAP 3, POKE 2, STATIC_TOUCH 2, STROKE 2, RUB 1, PAT 3, IMPACT 2
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000015`
- Observed matrix update rate: 52.71–53.21 Hz
- Frames per accepted trial: 743–748; all matrices finite and shaped `[T,18,29]`
- Status: block passed; session progress 15/35 Gold, overall progress 15/315 Gold

## Stage 3 Gold collection — operator_01/session_01 block 4

- Branch: `stage-3-gold-collection`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_01.csv` (seed 20260821)
- GPU: not used
- Attempts cumulative: 21 total; 20 VALID Gold; 1 REDO
- Labels cumulative: TAP 3, POKE 2, STATIC_TOUCH 3, STROKE 4, RUB 3, PAT 3, IMPACT 2
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000020`
- Observed matrix update rate: 52.71–53.21 Hz
- Frames per accepted trial: 743–748; all matrices finite and shaped `[T,18,29]`
- Status: block passed; session progress 20/35 Gold, overall progress 20/315 Gold

## Stage 3 Gold collection — operator_01/session_01 block 5

- Branch: `stage-3-gold-collection`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_01.csv` (seed 20260821)
- GPU: not used
- Attempts cumulative: 26 total; 25 VALID Gold; 1 REDO
- Labels cumulative: TAP 4, POKE 2, STATIC_TOUCH 5, STROKE 4, RUB 3, PAT 4, IMPACT 3
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000025`
- Observed matrix update rate: 52.71–53.21 Hz
- Frames per accepted trial: 743–749; all matrices finite and shaped `[T,18,29]`
- Status: block passed; session progress 25/35 Gold, overall progress 25/315 Gold

## Stage 3 Gold collection — operator_01/session_01 block 6

- Branch: `stage-3-gold-collection`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_01.csv` (seed 20260821)
- GPU: not used
- Attempts cumulative: 31 total; 30 VALID Gold; 1 REDO
- Labels cumulative: TAP 4, POKE 5, STATIC_TOUCH 5, STROKE 4, RUB 5, PAT 4, IMPACT 3
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000030`
- Observed matrix update rate: 52.70–53.21 Hz
- Frames per accepted trial: 743–749; all matrices finite and shaped `[T,18,29]`
- Status: block passed; session progress 30/35 Gold, overall progress 30/315 Gold

## Stage 3 Gold collection — operator_01/session_01 complete

- Branch: `stage-3-gold-collection`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_01.csv` (seed 20260821)
- GPU: not used
- Attempts: 36 total; 35 VALID Gold; 1 REDO
- Class balance: exactly 5 each for TAP, POKE, STATIC_TOUCH, STROKE, RUB, PAT, IMPACT
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000035`
- Observed matrix update rate: min 52.70, mean 52.93, max 53.21 Hz
- Host poll rate: min 186.45, mean 187.14, max 187.95 Hz
- Frames per accepted trial: 743–749; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -23 to 28
- Artifact: current ignored `data/processed/manifests/gold_manifest.csv` with 35 rows
- Status: session gate passed; operator_01 progress 35/105; overall progress 35/315

## Stage 3 Gold collection — operator_01/session_02 start

- Branch: `stage-3-gold-collection`
- Config: real SDK, new process/device initialization, 4-second capture,
  5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_02.csv` (seed 20260822)
- GPU: not used
- Collection timing note: started on the same date shortly after session_01 at
  the project owner's request; session ID, random order, and device initialization
  are independent, but the preferred longer time separation was not used
- Status: first 5-trial block launched; no session_02 result claimed yet

## Stage 3 Gold collection — operator_01/session_02 block 1

- Branch: `stage-3-gold-collection`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_02.csv` (seed 20260822)
- GPU: not used
- Session attempts: 5 total; 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 2, TAP 1, STATIC_TOUCH 1, STROKE 1
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000005`
- Observed matrix update rate: 52.95–53.21 Hz
- Frames per accepted trial: 742–750; all matrices finite and shaped `[T,18,29]`
- Status: block passed; session_02 progress 5/35; overall progress 40/315 Gold

## Stage 3 Gold collection — operator_01/session_02 block 2

- Branch: `stage-3-gold-collection`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_02.csv` (seed 20260822)
- GPU: not used
- Session attempts: 10 total; 10 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 2, POKE 1, RUB 1, STATIC_TOUCH 1, STROKE 1, TAP 1
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000010`
- Observed matrix update rate: min 52.95, mean 53.01, max 53.21 Hz
- Host poll rate: 185.99–188.21 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -14 to 30
- Status: block passed; session_02 progress 10/35; overall progress 45/315 Gold

## Stage 3 Gold collection — operator_01/session_02 block 3

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_02.csv` (seed 20260822)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_02 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 15 total; 15 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 3, POKE 2, RUB 2, STATIC_TOUCH 1, STROKE 2, TAP 2
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000015`; all attempt numbers are 1
- Observed matrix update rate: min 52.95, mean 52.99, max 53.21 Hz
- Host poll rate: min 185.99, mean 187.14, max 188.21 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -14 to 30
- Status: block passed; session_02 progress 15/35; overall progress 50/315 Gold

## Stage 3 Gold collection — operator_01/session_02 block 4

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_02.csv` (seed 20260822)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_02 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 20 total; 20 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 4, POKE 3, RUB 2, STATIC_TOUCH 2, STROKE 3, TAP 3
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000020`; all attempt numbers are 1
- Observed matrix update rate: min 52.95, mean 52.98, max 53.21 Hz
- Host poll rate: min 185.99, mean 187.25, max 188.21 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -14 to 30
- Status: block passed; session_02 progress 20/35; overall progress 55/315 Gold

## Stage 3 Gold collection — operator_01/session_02 block 5

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_02.csv` (seed 20260822)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_02 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 25 total; 25 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 4, PAT 4, POKE 4, RUB 3, STATIC_TOUCH 4, STROKE 3, TAP 3
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000025`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.98, max 53.21 Hz
- Host poll rate: min 185.95, mean 187.18, max 188.21 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -23 to 30
- Status: block passed; session_02 progress 25/35; overall progress 60/315 Gold

## Stage 3 Gold collection — operator_01/session_02 block 6

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_02.csv` (seed 20260822)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_02 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 30 total; 30 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 5, PAT 5, POKE 4, RUB 3, STATIC_TOUCH 5, STROKE 3, TAP 5
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000030`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.97, max 53.21 Hz
- Host poll rate: min 185.95, mean 187.12, max 188.21 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -23 to 30
- Status: block passed; session_02 progress 30/35; overall progress 65/315 Gold

## Stage 3 Gold collection — operator_01/session_02 complete

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_02.csv` (seed 20260822)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_02 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored `data/raw/deepskin/operator_01/session_02` and `data/processed/manifests/gold_manifest.csv`
- Attempts: 35 total; 35 VALID Gold; 0 REDO/UNCERTAIN
- Class balance: exactly 5 each for TAP, POKE, STATIC_TOUCH, STROKE, RUB, PAT, IMPACT
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000035`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.96, max 53.21 Hz
- Host poll rate: min 184.44, mean 187.00, max 188.21 Hz
- Frames per accepted trial: 735–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -23 to 30
- Known quality flag: SDK touch state false in every frame; matrix signal remained nonzero
- Manifest: 70 Gold rows across the two completed sessions
- Status: session gate passed; operator_01 progress 70/105; overall progress 70/315

## Stage 3 Gold collection — operator_01/session_03 start

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, new process/device initialization, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_03.csv` (seed 20260823)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_03 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact path: ignored `data/raw/deepskin/operator_01/session_03`
- Preflight: canonical manifest has 70 Gold rows; order file exists; session target did not previously exist
- Collection timing note: started shortly after session_02 at the project owner's request; the preferred longer time separation was not used
- Status: first 5-trial block ready to launch; no session_03 result claimed yet

## Stage 3 Gold collection — operator_01/session_03 block 1

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_03.csv` (seed 20260823)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_03 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 5 total; 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 1, PAT 1, RUB 1, STATIC_TOUCH 1, TAP 1
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000005`; all attempt numbers are 1
- Observed matrix update rate: min 52.95, mean 52.96, max 52.96 Hz
- Host poll rate: min 185.99, mean 187.34, max 187.75 Hz
- Frames per accepted trial: 741–748; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -5 to 25
- Status: block passed; session_03 progress 5/35; overall progress 75/315 Gold

## Stage 3 Gold collection — operator_01/session_03 block 2

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_03.csv` (seed 20260823)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_03 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 10 total; 10 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 1, RUB 2, STATIC_TOUCH 2, STROKE 1, TAP 1
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000010`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.93, max 53.21 Hz
- Host poll rate: min 185.99, mean 187.29, max 188.25 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -7 to 26
- Status: block passed; session_03 progress 10/35; overall progress 80/315 Gold

## Stage 3 Gold collection — operator_01/session_03 block 3

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_03.csv` (seed 20260823)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_03 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 15 total; 15 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 2, POKE 1, RUB 3, STATIC_TOUCH 3, STROKE 2, TAP 1
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000015`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.96, max 53.21 Hz
- Host poll rate: min 185.99, mean 187.21, max 188.25 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -7 to 26
- Status: block passed; session_03 progress 15/35; overall progress 85/315 Gold

## Stage 3 Gold collection — operator_01/session_03 block 4

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_03.csv` (seed 20260823)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_03 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 20 total; 20 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 4, PAT 4, POKE 2, RUB 3, STATIC_TOUCH 3, STROKE 2, TAP 2
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000020`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.96, max 53.21 Hz
- Host poll rate: min 185.99, mean 187.19, max 188.25 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -16 to 26
- Status: block passed; session_03 progress 20/35; overall progress 90/315 Gold

## Stage 3 Gold collection — operator_01/session_03 block 5

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_03.csv` (seed 20260823)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_03 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 25 total; 25 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 4, PAT 4, POKE 3, RUB 4, STATIC_TOUCH 4, STROKE 3, TAP 3
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000025`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.94, max 53.21 Hz
- Host poll rate: min 185.99, mean 187.19, max 188.25 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -16 to 26
- Status: block passed; session_03 progress 25/35; overall progress 95/315 Gold

## Stage 3 Gold collection — operator_01/session_03 block 6

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_03.csv` (seed 20260823)
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_03 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 30 total; 30 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 5, PAT 5, POKE 4, RUB 4, STATIC_TOUCH 5, STROKE 4, TAP 3
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000030`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.94, max 53.21 Hz
- Host poll rate: min 185.99, mean 187.20, max 188.25 Hz
- Frames per accepted trial: 741–750; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -16 to 26
- Status: block passed; session_03 progress 30/35; overall progress 100/315 Gold

## Stage 3 Gold collection — operator_01/session_03 and operator_01 complete

- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_01_session_03.csv` (seed 20260823)
- Commands: standard session runner in 5-trial blocks; final REDO retry used `--max-new-trials 1`
- GPU: not used
- Artifact paths: ignored `data/raw/deepskin/operator_01/session_03` and `data/processed/manifests/gold_manifest.csv`
- Session_03 attempts: 36 total; 35 VALID Gold; 1 REDO; 0 UNCERTAIN
- Session_03 class balance: exactly 5 each for TAP, POKE, STATIC_TOUCH, STROKE, RUB, PAT, IMPACT
- REDO handling: planned `trial_000032` attempt 1 remained immutable as REDO; attempt 2 entered Gold
- Operator_01 aggregate: 105 Gold across three 35-trial sessions; exactly 15 per class
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000035` within every session
- Aggregate observed matrix update rate: min 52.70, mean 52.95, max 53.21 Hz
- Aggregate host poll rate: min 184.44, mean 187.10, max 188.25 Hz
- Frames per accepted trial: 735–750; all matrices finite and shaped `[T,18,29]`
- Aggregate signal range: -23 to 30
- Known quality flag: SDK touch state false in every frame; matrix signal remained nonzero
- Status: session_03 and operator_01 gates passed; overall progress 105/315 Gold

## Stage 3 Gold collection — operator_02/session_01 start

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, new process/device initialization, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_01.csv` (seed 20260921)
- Command: `python scripts/record_session.py --operator-id operator_02 --session-id session_01 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact path: ignored `data/raw/deepskin/operator_02/session_01`
- Participant gate: project owner confirmed that operator_02 is prepared; distinct-participant identity is recorded only as the pseudonymous operator ID
- Preflight: canonical manifest has 105 operator_01 Gold rows; order file exists; target directory did not previously exist
- Status: first 5-trial block ready to launch; no operator_02 result claimed yet

## Stage 3 Gold collection — operator_02/session_01 block 1

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_01.csv` (seed 20260921)
- Command: `python scripts/record_session.py --operator-id operator_02 --session-id session_01 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 5 total; 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 1, PAT 1, STATIC_TOUCH 1, STROKE 2
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000005`; all attempt numbers are 1
- Observed matrix update rate: min 52.71, mean 52.91, max 53.21 Hz
- Host poll rate: min 186.24, mean 186.83, max 187.20 Hz
- Frames per accepted trial: 742–746; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -2 to 23
- Status: block passed; operator_02/session_01 progress 5/35; overall progress 110/315 Gold

## Stage 3 Gold collection — operator_02/session_01 block 2

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_01.csv` (seed 20260921)
- Command: `python scripts/record_session.py --operator-id operator_02 --session-id session_01 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 10 total; 10 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 1, POKE 1, STATIC_TOUCH 1, STROKE 3, TAP 1
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000010`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.91, max 53.21 Hz
- Host poll rate: min 185.45, mean 186.77, max 187.45 Hz
- Frames per accepted trial: 739–747; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -7 to 23
- Status: block passed; operator_02/session_01 progress 10/35; overall progress 115/315 Gold

## Stage 3 Gold collection — operator_02/session_01 block 3

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_01.csv` (seed 20260921)
- Command: `python scripts/record_session.py --operator-id operator_02 --session-id session_01 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 15 total; 15 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 1, POKE 2, RUB 1, STATIC_TOUCH 2, STROKE 4, TAP 2
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000015`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.87, max 53.21 Hz
- Host poll rate: min 185.45, mean 186.78, max 187.45 Hz
- Frames per accepted trial: 739–747; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -7 to 25
- Status: block passed; operator_02/session_01 progress 15/35; overall progress 120/315 Gold

## Stage 3 Gold collection — operator_02/session_01 block 4

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_01.csv` (seed 20260921)
- Command: `python scripts/record_session.py --operator-id operator_02 --session-id session_01 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 20 total; 20 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 2, POKE 3, RUB 4, STATIC_TOUCH 2, STROKE 4, TAP 2
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000020`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.89, max 53.21 Hz
- Host poll rate: min 185.45, mean 186.64, max 187.45 Hz
- Frames per accepted trial: 739–747; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -7 to 27
- Status: block passed; operator_02/session_01 progress 20/35; overall progress 125/315 Gold

## Stage 3 Gold collection — operator_02/session_01 block 5

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_01.csv` (seed 20260921)
- Command: `python scripts/record_session.py --operator-id operator_02 --session-id session_01 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Artifact paths: ignored raw session directory and `data/processed/manifests/gold_manifest.csv`
- Session attempts: 25 total; 25 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 4, PAT 3, POKE 4, RUB 4, STATIC_TOUCH 4, STROKE 4, TAP 2
- Planned IDs: contiguous and unique from `trial_000001` through `trial_000025`; all attempt numbers are 1
- Observed matrix update rate: min 52.70, mean 52.91, max 53.21 Hz
- Host poll rate: min 185.45, mean 186.69, max 187.50 Hz
- Frames per accepted trial: 739–747; all matrices finite and shaped `[T,18,29]`
- Signal range across accepted trials: -7 to 27
- Status: block passed; operator_02/session_01 progress 25/35; overall progress 130/315 Gold

## Stage 3 protocol correction — pulse_count recollection initiated

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Trigger: project owner reported that prior `pulse_count` instructions were misunderstood
- Correct interpretation: N separated short contacts; fully lift after each contact; move about 1–2 cm to a nearby location; do not slide or repeatedly press in place
- Collection action: stopped the active operator_02 recorder after 29 saved attempts to avoid expanding invalid data
- Affected existing Gold: 39 total — 10 in each operator_01 session and 9 in operator_02/session_01
- Recollection plan: `protocol/recollection_plans/pulse_count_v1.csv`; old raw trials remain immutable, but attempts below each listed minimum are excluded from Gold
- Code changes: recollection-plan loader, recorder plan mode and explicit pulse instructions, manifest minimum-attempt filtering
- Verification: focused recollection regression passed; all 13 tests passed
- Manifest audit: canonical Gold reduced from the raw 134 valid trials to 95 eligible rows; all 39 affected prior attempts are excluded
- GPU: not used
- Status: correction gate passed; recollection pending; headline progress is temporarily 95/315 eligible Gold

## Stage 3 pulse_count recollection — operator_02 block 1

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Command: `python scripts/record_session.py --operator-id operator_02 --session-id session_01 --recollection-plan protocol/recollection_plans/pulse_count_v1.csv --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- GPU: not used
- Replacements accepted: planned trials 000004, 000012, 000016, 000017, 000018; all are VALID attempt 2
- Frames: 743–746; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.95, mean 52.96, max 52.96 Hz
- Signal range: -3 to 25
- Manifest rule: original attempts remain excluded; only replacement attempts enter Gold
- Status: block passed; 5/39 affected trials replaced; operator_02 has 4 pulse replacements remaining; eligible Gold 100/315

## Stage 3 pulse_count recollection — operator_02 complete

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Commands: two plan-mode batches, first with five replacements and second with four
- GPU: not used
- Replacements accepted: 9/9 affected operator_02/session_01 planned trials; all are VALID attempt 2
- Frames: 740–746; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.93, max 52.96 Hz
- Signal range: -3 to 25
- Manifest rule: all nine original misunderstood attempts remain excluded; only replacements enter Gold
- Status: operator_02 pulse recollection gate passed; 9/39 total affected trials replaced; eligible Gold 104/315

## Stage 3 Gold collection — operator_02/session_01 resumed through trial 34

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- New planned trials: 000030–000034; all five VALID Gold on attempt 1
- Pulse handling: trial 000031 used the corrected separated-contact/lift/move rule
- Frames: 743–746; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.71, mean 52.91, max 52.96 Hz
- Signal range: -2 to 23
- Session balance so far: six classes have 5 Gold; STROKE has 4 Gold
- Status: block passed; operator_02/session_01 has 34/35 eligible Gold; overall eligible progress 109/315

## Stage 3 Gold collection — operator_02/session_01 complete after pulse correction

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Final command: standard session runner with `--max-new-trials 1` for planned trial 000035
- GPU: not used
- Eligible session rows: 35 unique planned trials; exactly 5 per class
- Pulse replacements: 9 corrected attempt-2 rows included; all nine misunderstood attempt-1 rows excluded
- Raw VALID directories: 44, reflecting 35 current selections plus 9 immutable superseded attempts
- Frames: 739–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.92, max 53.21 Hz
- Host poll rate: min 185.45, mean 186.72, max 187.50 Hz
- Signal range: -7 to 27
- Status: corrected session gate passed; operator_02 progress 35/105; operator_01 has 30 pulse replacements pending; overall eligible progress 110/315

## Stage 3 pulse_count recollection — operator_01/session_01 start

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Command: `python scripts/record_session.py --operator-id operator_01 --session-id session_01 --recollection-plan protocol/recollection_plans/pulse_count_v1.csv --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- Participant gate: project owner confirmed the original operator_01 is prepared and understands the corrected pulse rule
- Preflight: canonical manifest has 110 eligible rows; session_01 has 10 targets; trial 000001 requires attempt 3 and the other targets require attempt 2
- GPU: not used
- Status: first five replacement trials ready to launch; no new replacement result claimed yet

## Stage 3 pulse_count recollection — operator_01/session_01 block 1

- Date: 2026-08-21
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Replacements accepted: planned 000001, 000008, 000012, 000015, 000017
- Attempt rule: planned 000001 entered as attempt 3; the other four entered as attempt 2; all are VALID Gold
- Frames: 741–744; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.95, mean 53.00, max 53.20 Hz
- Signal range: -2 to 24
- Manifest rule: all superseded attempts remain excluded
- Status: block passed; 14/39 total affected trials replaced; eligible Gold 115/315

## Stage 3 pulse_count recollection — operator_01/session_01 complete

- Date: 2026-08-21
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Replacements accepted: 10/10 session targets; planned 000001 uses attempt 3 and the remaining nine use attempt 2
- Eligible session rows: 35 unique planned trials; exactly 5 per class
- Frames across replacements: 741–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate across replacements: min 52.71, mean 53.00, max 53.21 Hz
- Signal range across replacements: -3 to 24
- Manifest rule: all misunderstood attempts remain excluded
- Status: session correction gate passed; 19/39 total affected trials replaced; eligible Gold 120/315

## Stage 3 pulse_count recollection — operator_01/session_02 start

- Date: 2026-08-21
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Command: plan-mode session runner with `--max-new-trials 5`
- Preflight: 10 session_02 targets, all requiring attempt 2
- Status: first five replacements ready to launch; no session_02 replacement result claimed yet

## Stage 3 pulse_count recollection — operator_01/session_02 block 1

- Date: 2026-08-21
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Replacements accepted: planned 000007, 000008, 000009, 000011, 000013; all VALID attempt 2
- Frames: 736–745; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.71, mean 52.91, max 52.96 Hz
- Signal range: -2 to 21
- Manifest rule: superseded attempts remain excluded
- Status: block passed; 24/39 total affected trials replaced; eligible Gold 125/315

## Stage 3 pulse_count recollection — operator_01/session_02 complete

- Date: 2026-08-21
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Replacements accepted: 10/10 session targets; all VALID attempt 2
- Eligible session rows: 35 unique planned trials; exactly 5 per class
- Frames across replacements: 736–745; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate across replacements: min 52.71, mean 52.93, max 52.96 Hz
- Signal range across replacements: -3 to 21
- Manifest rule: all misunderstood attempts remain excluded
- Status: session correction gate passed; 29/39 total affected trials replaced; eligible Gold 130/315

## Stage 3 pulse_count recollection — operator_01/session_03 start

- Date: 2026-08-21
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Command: plan-mode session runner with `--max-new-trials 5`
- Preflight: 10 session_03 targets, all requiring attempt 2
- Status: first five replacements ready to launch; no session_03 replacement result claimed yet

## Stage 3 pulse_count recollection — operator_01/session_03 block 1

- Date: 2026-08-21
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Replacements accepted: planned 000002, 000003, 000006, 000012, 000015; all VALID attempt 2
- Frames: 741–748; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.95, max 53.21 Hz
- Signal range: -3 to 28
- Manifest rule: superseded attempts remain excluded
- Status: block passed; 34/39 total affected trials replaced; eligible Gold 135/315

## Stage 3 pulse_count correction — complete

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Plan: `protocol/recollection_plans/pulse_count_v1.csv`
- Final replacements: operator_01/session_03 remaining five VALID attempt-2 trials
- Correction total: 39/39 affected planned trials replaced and selected at or above their declared minimum attempt
- Session gates: operator_01/session_01, session_02, session_03, and operator_02/session_01 each contain 35 unique Gold rows with exactly 5 per class
- Aggregate eligible data: 140 Gold; exactly 20 per class; operator_01 105 and operator_02 35
- Frames: 735–750; every matrix finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.94, max 53.21 Hz
- Host poll rate: min 184.44, mean 186.85, max 188.25 Hz
- Signal range: -23 to 28
- Known quality flag: SDK touch state remains false in every frame
- Verification: all 13 unit tests passed; manifest rebuild after cleanup exactly matched 140 canonical rows
- Cleanup: removed 40 superseded raw attempt directories (5,669,241 bytes) and all temporary manifests; cleanup is not recoverable from the workspace
- Status: pulse correction gate passed; overall eligible progress 140/315; normal collection may resume

## Stage 3 Gold collection — operator_02/session_02 start

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, new process/device initialization, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_02.csv` (seed 20260922)
- Command: `python scripts/record_session.py --operator-id operator_02 --session-id session_02 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- Participant gate: project owner confirmed the original operator_02 is prepared and understands the corrected pulse rule
- Preflight: canonical manifest has 140 eligible rows; order file exists; target directory did not previously exist
- GPU: not used
- Status: first five trials ready to launch; no session_02 result claimed yet

## Stage 3 Gold collection — operator_03/session_02 block 7 and session closeout
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_02.csv` (seed 20261022)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 35 total; seventh block 5 VALID Gold; 0 REDO/UNCERTAIN
- Final class balance: IMPACT 5, PAT 5, POKE 5, RUB 5, STATIC_TOUCH 5, STROKE 5, TAP 5
- Planned IDs: seventh block contiguous and unique from 000031 through 000035; all attempt numbers are 1
- Frames: 741–748; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.95, mean 52.96, max 52.96 Hz
- Host poll rate: min 185.99, mean 186.89, max 187.70 Hz
- Signal range: -4 to 24
- Status: block passed and session complete; operator_03/session_02 progress 35/35; overall eligible progress 280/315

## Stage 3 Gold collection — operator_03/session_03 block 1
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_03.csv` (seed 20261023)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Launch note: initial launch produced no session directory; empty candidate manifest was removed and the batch was relaunched successfully
- Session attempts: 5 total; 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: POKE 1, STATIC_TOUCH 1, STROKE 2, TAP 1
- Planned IDs: contiguous and unique from 000001 through 000005; all attempt numbers are 1
- Frames: 741–746; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.95, mean 52.95, max 52.96 Hz
- Host poll rate: min 185.95, mean 186.87, max 187.25 Hz
- Signal range: -3 to 22
- Status: block passed; operator_03/session_03 progress 5/35; overall eligible progress 285/315

## Stage 3 Gold collection — operator_03/session_03 block 2
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_03.csv` (seed 20261023)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 10 total; second block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 1, PAT 1, POKE 1, STATIC_TOUCH 2, STROKE 3, TAP 2
- Planned IDs: second block contiguous and unique from 000006 through 000010; all attempt numbers are 1
- Frames: 738–749; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.95, max 53.20 Hz
- Host poll rate: min 185.19, mean 187.11, max 187.95 Hz
- Signal range: -3 to 26
- Status: block passed; operator_03/session_03 progress 10/35; overall eligible progress 290/315

## Stage 3 Gold collection — operator_03/session_03 block 3
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_03.csv` (seed 20261023)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 15 total; third block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 2, PAT 3, POKE 1, RUB 2, STATIC_TOUCH 2, STROKE 3, TAP 2
- Planned IDs: third block contiguous and unique from 000011 through 000015; all attempt numbers are 1
- Frames: 737–746; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.71, mean 52.91, max 52.96 Hz
- Host poll rate: min 184.99, mean 186.63, max 187.20 Hz
- Signal range: -2 to 25
- Status: block passed; operator_03/session_03 progress 15/35; overall eligible progress 295/315

## Stage 3 Gold collection — operator_03/session_03 block 4
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_03.csv` (seed 20261023)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 20 total; fourth block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 2, PAT 4, POKE 2, RUB 4, STATIC_TOUCH 2, STROKE 3, TAP 3
- Planned IDs: fourth block contiguous and unique from 000016 through 000020; all attempt numbers are 1
- Frames: 743–748; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.95, mean 52.96, max 52.96 Hz
- Host poll rate: min 186.45, mean 187.08, max 187.75 Hz
- Signal range: -2 to 23
- Status: block passed; operator_03/session_03 progress 20/35; overall eligible progress 300/315

## Stage 3 Gold collection — operator_03/session_03 block 5
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_03.csv` (seed 20261023)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 25 total; fifth block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 4, PAT 5, POKE 4, RUB 4, STATIC_TOUCH 2, STROKE 3, TAP 3
- Planned IDs: fifth block contiguous and unique from 000021 through 000025; all attempt numbers are 1
- Frames: 739–743; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.90, max 52.96 Hz
- Host poll rate: min 185.45, mean 186.12, max 186.45 Hz
- Signal range: -2 to 26
- Status: block passed; operator_03/session_03 progress 25/35; overall eligible progress 305/315

## Stage 3 Gold collection — operator_03/session_03 block 6
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_03.csv` (seed 20261023)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 30 total; sixth block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 4, PAT 5, POKE 4, RUB 4, STATIC_TOUCH 4, STROKE 4, TAP 5
- Planned IDs: sixth block contiguous and unique from 000026 through 000030; all attempt numbers are 1
- Frames: 740–744; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.95, mean 53.01, max 53.21 Hz
- Host poll rate: min 185.74, mean 186.49, max 186.75 Hz
- Signal range: -3 to 23
- Status: block passed; operator_03/session_03 progress 30/35; overall eligible progress 310/315

## Stage 3 Gold collection — operator_03/session_03 block 7 and stage closeout
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_03.csv` (seed 20261023)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 35 total; seventh block 5 VALID Gold; 0 REDO/UNCERTAIN
- Final session balance: IMPACT 5, PAT 5, POKE 5, RUB 5, STATIC_TOUCH 5, STROKE 5, TAP 5
- Planned IDs: seventh block contiguous and unique from 000031 through 000035; all attempt numbers are 1
- Final-block frames: 741–749; all matrices finite and shaped `[T,18,29]`
- Final-block matrix update rate: min 52.71, mean 52.96, max 53.21 Hz
- Final-block host poll rate: min 185.99, mean 187.10, max 188.00 Hz
- Final-block signal range: -3 to 25
- Dataset audit: 315 Gold rows; 315 unique `(operator, session, planned_trial)` keys; 9 sessions of 35 rows; every session has 7 classes x 5 trials; every class has 45 trials globally
- Dataset integrity: all 315 matrices finite, shaped `[T,18,29]`, and consistent with manifest/metadata; global frames 735–751; update rate 52.70–53.21 Hz; host poll rate 184.44–188.46 Hz; signal range -23 to 28
- Status: block passed, operator_03/session_03 complete 35/35, and Stage 3 collection target complete 315/315

## Stage 4 — three-policy flip augmentation ablation
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Data: canonical 315-row Gold manifest; all evaluation rows are original real trials
- Model/features: standardized class-balanced RBF-SVM; 51 pressure/area/temporal/centroid/movement/direction features
- Split: nested 3-fold Leave-One-Operator-Out; augmentation only in training partitions
- Search: C 0.1/1/10/100; gamma scale/0.01/0.1/1; inner validation selected by Macro F1
- Policies: none 1x; horizontal 2x; horizontal+vertical 4x (original/H/V/HV)
- Environment: Python 3.12; scikit-learn 1.9.0; scipy 1.18.0; CPU training; RTX 5060 Ti not used because RBF-SVM has no CUDA path
- Smoke: 42 balanced original evaluation rows; all three policies completed; smoke metrics not used for conclusions
- Full results: none Macro F1 0.7988 / balanced accuracy 0.7968; horizontal 0.7810 / 0.7810; horizontal+vertical 0.8316 / 0.8286
- Best-candidate fold Macro F1: operator_01 0.8395, operator_02 0.8782, operator_03 0.7800
- Audit: all policies evaluated identical 315 unique keys; 105 untouched test rows per fold; training/test operator overlap rejected; 15 tests passed
- Artifacts: `artifacts/experiments/flip_ablation_smoke_v1/`, `artifacts/experiments/flip_ablation_full_v1/`, `artifacts/stage_reports/stage_4_flip_ablation.md`
- Status: experiment passed; horizontal-only rejected; horizontal+vertical is the current candidate, subject to the documented three-operator and left-hand-only limitations

## Stage 5 — final target-only model package
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Input: canonical 315-row Gold manifest
- Recipe: all real trials with original/horizontal/vertical/both transforms; 1260 fitted rows
- Model: StandardScaler + class-balanced RBF-SVM, C=10, gamma=0.01
- Selection basis: modal configuration from the best policy's nested Leave-One-Operator-Out folds; no outer-test adaptation during final fitting
- GPU: not used; RBF-SVM ran on CPU
- Package: `models/deepskin_social_touch_v1/`
- Contents: model, training manifest, 51-feature schema, seven-class label map, frozen config, model card, SHA-256 checksums
- Audit: model reload passed; 315 unique manifest keys; model/schema dimension 51; labels/classes match; six payload checksums valid
- End-to-end smoke: `operator_03/session_03/trial_000035` predicted `STROKE`, matching Gold label
- Tests: 15 passed
- Generalization estimate: nested LOPO Macro F1 0.8316, balanced accuracy 0.8286; no training score claimed
- Status: final offline model package complete; next gate is real-time SDK inference integration and live hardware validation

## Stage 6 — live inference smoke 01 (protocol-invalid)
- Date: 2026-08-21
- Expected: STROKE
- Prediction: RUB; STROKE ranked third
- Hardware: valid finite `[743,18,29]` window; 743 frames over 3985 ms; host poll rate 186.45 Hz; signal range -2 to 18
- Model integrity: recorded model SHA-256 matches the packaged final model
- Root cause: operator prompt incorrectly requested continuous/back-and-forth motion, which matches RUB return-cycle semantics rather than single-direction STROKE
- Disposition: inference plumbing passed, classification claim invalidated by protocol mismatch; result retained for audit and excluded from model-performance claims
- Fix: explicit class-specific prompts added; corrected STROKE retest required

## Stage 6 — live inference smoke 02 (passed)
- Date: 2026-08-21
- Expected/predicted: STROKE / STROKE; expected match true
- Top-3: STROKE 6.305, TAP 5.293, RUB 4.267
- Hardware: finite `[743,18,29]` window; 743 frames over 3985 ms; host poll rate 186.45 Hz; signal range -2 to 18
- Model integrity: recorded SHA-256 matches the packaged final model
- Protocol: one left-to-right path followed by complete lift-off; no return rubbing
- Status: corrected single-class live inference pipeline passed; next minimal validation is one protocol-controlled live trial for each of the seven classes

## Stage 6 — seven-class live smoke 01
- Date: 2026-08-21
- Result: 3/7 Top-1 matches
- Correct: STATIC_TOUCH, STROKE, IMPACT
- Confusions: RUB→STATIC_TOUCH, TAP→POKE, POKE→TAP, PAT→IMPACT
- Top-2 note: the expected class was second for every misclassification
- Hardware integrity: all seven matrices finite `[T,18,29]`; 742–748 frames; host poll rate 186.20–187.75 Hz; model hashes match
- Interpretation: confirms the predicted TAP/POKE ambiguity and adjacent-class uncertainty; one sample/class is a smoke result, not a performance estimate
- Diagnostic limitation: suite saved JSON summaries but no raw matrices, so event segmentation and waveform analysis cannot be performed on this batch
- Status: live plumbing passed but seven-class recognition gate did not pass; preserve results and collect targeted raw-backed diagnostics before changing the model

## Stage 6 — raw-backed TAP diagnostic 01
- Date: 2026-08-21
- Expected/predicted: TAP / TAP; Top-1 match
- Raw preservation: JSON and same-stem NPZ created; SHA-256 linkage verified; matrix finite `[740,18,29]`
- Hardware: 740 frames over 3984 ms; host poll rate 185.74 Hz; signal range -2 to 12
- Event proxy: peak >=3 spans approximately 531–750 ms (42 host-polled frames, 219 ms); peak max 12; max area at value >=2 is 46 cells
- Interpretation: the short event occupies about 5.5% of the full four-second window, supporting an event-segmentation experiment; spatial activation is not point-like despite a fingertip TAP
- Status: raw-capture fix verified; collect a matched POKE raw diagnostic before defining segmentation or changing features

## Stage 6 — raw-backed POKE diagnostic 01
- Date: 2026-08-21
- Expected/predicted: POKE / POKE; Top-1 match
- Raw preservation: JSON/NPZ SHA-256 linkage verified; finite `[739,18,29]` matrix
- Hardware: 739 frames over 3984 ms; host poll rate 185.49 Hz; signal range -2 to 18
- Main continuous event proxy: approximately 453–1890 ms (1.44 s), peak cell 18, total positive peak 331, max area at value >=2 is 51 cells
- Matched TAP comparison: TAP main activity about 0.22 s, peak cell 12, total positive peak 312, max area 46 cells
- Interpretation: peak magnitude and area overlap, while temporal duration differs strongly in this pair; scattered low-level post-event runs show that naive first-to-last threshold duration is invalid
- Status: evidence supports an event-segmentation ablation using a bridged longest active run; do not change the final model until grouped offline validation passes

## Stage 6 — event segmentation grouped ablation
- Date: 2026-08-21
- Segmenter: baseline-relative peak threshold, <=100 ms gap bridging, longest active run, 100 ms boundary padding
- Validation: same nested Leave-One-Operator-Out and identical 315 unique outer-test keys
- Current final model: unsegmented H/V/HV Macro F1 0.8316; fold mean/std 0.8326/0.0404
- Segmented no-flip: Macro F1 0.8378; balanced accuracy 0.8381; fold mean/std 0.8380/0.0637
- Segmented H/V/HV: Macro F1 0.8095; balanced accuracy 0.8095
- Pair effect: POKE F1 0.6598→0.7253; TAP F1 0.7347→0.7957; POKE→TAP 10→6; TAP→POKE unchanged at 7
- Risk: overall gain only 0.0062, fold variance increased, operator_03 fell to 0.7526, and IMPACT/PAT worsened
- Tests/smoke: 16 tests passed; segmented balanced smoke completed before full run
- Artifacts: `artifacts/experiments/flip_ablation_segmented_smoke_v1/`, `artifacts/experiments/flip_ablation_segmented_full_v1/`, `artifacts/stage_reports/stage_6_event_segmentation.md`
- Status: replacement gate not met; retain packaged final model and collect repeated raw-backed TAP/POKE live diagnostics

## Stage 6 — TAP/POKE protocol correction and recollection gate
- Date: 2026-08-21
- Evidence: original protocol used only `single contact` for TAP and `clear inward pressure` for POKE, while both had LIGHT/NORMAL/FIRM variants and no duration/release boundary
- Gold audit: TAP median event proxy 297 ms; POKE 516 ms; five TAP >=500 ms and four POKE <=300 ms
- Recollection scope: nine high-risk trials only; duration is an audit flag, not an automatic relabeling rule
- Corrected TAP: one fast 100–300 ms contact, immediate full lift, no deliberate inward dwell
- Corrected POKE: fingertip inward press with 500–1500 ms short dwell, full lift, not a quick tap
- Plan: `protocol/recollection_plans/gold_corrections_v2.csv`; retains all 39 pulse targets and adds nine TAP/POKE targets (48 total)
- Gate test: 16 tests passed; pre-recollection candidate contained 306 rows, excluding exactly the nine intended records; canonical manifest remained 315
- Status: protocol and gate ready; begin targeted recollection without deleting or relabeling original attempts

## Stage 6 — TAP/POKE recollection block 1 (2/9)
- Date: 2026-08-21
- Scope: operator_01/session_01 trial_000010 and trial_000021, both TAP attempt 2
- Result: 2/2 VALID Gold; matrices finite `[T,18,29]`; host poll rates 186.50 and 188.71 Hz
- Event proxy durations: 250 ms and 203 ms, both within the corrected TAP target of approximately 100–300 ms
- Gate candidate: 308 rows, restoring exactly these two targets; canonical manifest intentionally remained at the prior 315 rows until all nine replacements pass
- Status: block passed; recollection progress 2/9

## Stage 6 — TAP/POKE recollection block 2 and cleanup (5/9)
- Date: 2026-08-21
- Scope: operator_01/session_03 trial_000016 POKE, trial_000031 TAP, trial_000034 POKE; all attempt 2
- Result: 3/3 VALID Gold; finite `[T,18,29]`; host poll rates 186.24–187.25 Hz
- Event proxy durations: POKE 1234 ms, TAP 203 ms, POKE 1766 ms; the last is slightly above the nominal 1500 ms target but accepted as a clear sustained inward press within approximate protocol tolerance
- Canonical manifest: promoted to 311 rows and verified to reference attempt 2 for all five completed replacements
- Cleanup: deleted the five superseded attempt 1 raw directories from blocks 1–2 after path and manifest-reference validation; 661,870 bytes removed; these old directories are not recoverable from the workspace
- Preservation: four not-yet-recollected high-risk originals and all new valid attempts remain intact
- Status: block passed; recollection progress 5/9

## Stage 6 — TAP/POKE recollection block 3 and cleanup (7/9)
- Date: 2026-08-21
- Scope: operator_02/session_02 trial_000032 TAP and trial_000034 POKE, both attempt 2
- Result: 2/2 VALID Gold; finite `[T,18,29]`; host poll rates 186.50 and 186.45 Hz
- Event proxy durations: TAP 250 ms; POKE 1235 ms; both satisfy corrected operational targets
- Canonical manifest: promoted to 313 rows and verified to reference both attempt 2 paths
- Cleanup: deleted two superseded attempt 1 raw directories after validation; 262,940 bytes removed; not recoverable from workspace
- Status: block passed; recollection progress 7/9

## Stage 6 — TAP/POKE recollection block 4 and cleanup (8/9)
- Date: 2026-08-21
- Scope: operator_03/session_01 trial_000014 TAP
- Attempts: attempt 2 was REDO; attempt 3 was VALID Gold
- Valid event proxy duration: 219 ms; finite `[738,18,29]`; host poll rate 185.24 Hz; signal range -3 to 13
- Canonical manifest: promoted to 314 rows and verified to reference attempt 3
- Cleanup: deleted superseded attempt 1 and REDO attempt 2 after validation; 250,283 bytes removed; not recoverable from workspace
- Status: block passed; recollection progress 8/9

## Stage 6 — TAP/POKE recollection closeout (9/9)
- Date: 2026-08-21
- Final target: operator_03/session_02 trial_000015 POKE attempt 2
- Result: VALID Gold; event proxy 1109 ms; finite `[740,18,29]`; host poll 185.70 Hz; signal range -3 to 22
- Cleanup: deleted final superseded attempt 1 directory after manifest validation; 124,612 bytes removed; not recoverable from workspace
- Final corrected durations: TAP 203–250 ms across five replacements; POKE 1109–1766 ms across four replacements
- Dataset audit: 315 unique rows, no missing paths, all matrices finite `[T,18,29]`, nine sessions x 35, each class 45 globally
- Tests: 16 passed
- Status: targeted recollection complete 9/9; corrected canonical Gold restored to 315/315; prior trained model is now historical and three-policy retraining is required

## Stage 7 — corrected three-policy retraining and final model v2
- Date: 2026-08-21
- Corrected whole-window results: none 0.7851, horizontal 0.7872, H/V/HV 0.8089 Macro F1
- Corrected segmented results: none 0.8535, horizontal 0.8380, H/V/HV 0.8071 Macro F1
- Selected policy: event segmentation + no flip; Macro F1 0.8535; balanced accuracy 0.8540
- Fold Macro F1: operator_01 0.8745, operator_02 0.9061, operator_03 0.7801
- Pair improvement versus v1: TAP F1 0.7347→0.8817; POKE 0.6598→0.7312; direct TAP/POKE cross-confusions 17→7
- Tradeoff: IMPACT/PAT lower than v1 and fold variance higher; documented rather than hidden
- Package: `models/deepskin_social_touch_v2`; 315 real fitted rows; C=10; gamma=scale; 51 features
- Audit: 315 unique keys, model/schema dimension 51, segmentation flag true, checksums valid, corrected TAP and POKE end-to-end predictions correct, 16 tests passed
- Runtime: default live model switched from v1 to v2; v1 retained as historical comparison
- Status: offline v2 complete; repeat seven-class live validation before deployment acceptance

## Stage 8 — model v2 seven-class live smoke
- Date: 2026-08-21
- Model: `deepskin_social_touch_v2`, event segmentation enabled, model SHA-256 verified for every trial
- Result: 7/7 Top-1 matches; v1 comparison was 3/7
- Classes passed: STATIC_TOUCH, STROKE, RUB, TAP, POKE, PAT, IMPACT
- Raw audit: seven JSON + seven NPZ; all raw SHA-256 links valid; all matrices finite `[T,18,29]`
- Host poll range: 185.49–187.50 Hz
- Event durations: STATIC_TOUCH 2719 ms, STROKE 718 ms, RUB 2407 ms, TAP 188 ms, POKE 1234 ms, PAT 359 ms, IMPACT 391 ms
- Decision margin: Top-1 minus Top-2 approximately 1.0 or greater for all seven
- Interpretation: functional live pipeline gate passed; one sample/class is not a population performance estimate
- Status: v2 accepted for interface integration; formal generalization estimate remains nested LOPO Macro F1 0.8535

## Stage 3 Gold collection — operator_03/session_02 block 1

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_02.csv` (seed 20261022)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 5 total; 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 1, STATIC_TOUCH 2, STROKE 1, TAP 1
- Planned IDs: contiguous and unique from 000001 through 000005; all attempt numbers are 1
- Frames: 743–749; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.95, mean 52.96, max 52.96 Hz
- Host poll rate: min 186.50, mean 187.23, max 187.95 Hz
- Signal range: -3 to 25
- Status: block passed; operator_03/session_02 progress 5/35; overall eligible progress 250/315

## Stage 3 Gold collection — operator_03/session_02 block 2
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_02.csv` (seed 20261022)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 10 total; second block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 1, PAT 1, POKE 1, STATIC_TOUCH 4, STROKE 2, TAP 1
- Planned IDs: second block contiguous and unique from 000006 through 000010; all attempt numbers are 1
- Frames: 741–744; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.86, max 52.96 Hz
- Host poll rate: min 185.99, mean 186.43, max 186.75 Hz
- Signal range: -5 to 26
- Status: block passed; operator_03/session_02 progress 10/35; overall eligible progress 255/315

## Stage 3 Gold collection — operator_03/session_02 block 3
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_02.csv` (seed 20261022)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 15 total; third block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 2, PAT 2, POKE 2, RUB 2, STATIC_TOUCH 4, STROKE 2, TAP 1
- Planned IDs: third block contiguous and unique from 000011 through 000015; all attempt numbers are 1
- Frames: 740–746; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.71, mean 52.86, max 52.96 Hz
- Host poll rate: min 185.74, mean 186.83, max 187.20 Hz
- Signal range: -2 to 20
- Status: block passed; operator_03/session_02 progress 15/35; overall eligible progress 260/315

## Stage 3 Gold collection — operator_03/session_02 block 4
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_02.csv` (seed 20261022)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 20 total; fourth block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 2, POKE 3, RUB 4, STATIC_TOUCH 4, STROKE 3, TAP 1
- Planned IDs: fourth block contiguous and unique from 000016 through 000020; all attempt numbers are 1
- Frames: 741–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.95, mean 53.01, max 53.20 Hz
- Host poll rate: min 185.95, mean 186.93, max 187.50 Hz
- Signal range: -3 to 25
- Status: block passed; operator_03/session_02 progress 20/35; overall eligible progress 265/315

## Stage 3 Gold collection — operator_03/session_02 block 5
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_02.csv` (seed 20261022)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 25 total; fifth block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 4, PAT 2, POKE 4, RUB 4, STATIC_TOUCH 4, STROKE 4, TAP 3
- Planned IDs: fifth block contiguous and unique from 000021 through 000025; all attempt numbers are 1
- Frames: 743–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.96, mean 52.96, max 52.96 Hz
- Host poll rate: min 186.50, mean 186.90, max 187.50 Hz
- Signal range: -3 to 21
- Status: block passed; operator_03/session_02 progress 25/35; overall eligible progress 270/315

## Stage 3 Gold collection — operator_03/session_02 block 6
- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_02.csv` (seed 20261022)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 30 total; sixth block 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 4, PAT 5, POKE 5, RUB 4, STATIC_TOUCH 4, STROKE 4, TAP 4
- Planned IDs: sixth block contiguous and unique from 000026 through 000030; all attempt numbers are 1
- Frames: 743–748; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.95, mean 53.01, max 53.20 Hz
- Host poll rate: min 186.50, mean 187.38, max 187.75 Hz
- Signal range: -2 to 22
- Status: block passed; operator_03/session_02 progress 30/35; overall eligible progress 275/315

## Stage 3 Gold collection — operator_02/session_02 block 1

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_02.csv` (seed 20260922)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 5 total; 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 1, POKE 2, STATIC_TOUCH 1, STROKE 1
- Planned IDs: contiguous and unique from 000001 through 000005; all attempt numbers are 1
- Frames: 738–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.90, max 52.96 Hz
- Host poll rate: min 185.19, mean 186.36, max 187.50 Hz
- Signal range: -2 to 22
- Status: block passed; operator_02/session_02 progress 5/35; overall eligible progress 145/315

## Stage 3 Gold collection — operator_02/session_02 block 2

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_02.csv` (seed 20260922)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 10 total; 10 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 1, PAT 2, POKE 3, STATIC_TOUCH 2, STROKE 1, TAP 1
- Planned IDs: contiguous and unique from 000001 through 000010; all attempt numbers are 1
- Frames: 738–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.90, max 52.96 Hz
- Host poll rate: min 185.19, mean 186.54, max 187.50 Hz
- Signal range: -3 to 26
- Status: block passed; operator_02/session_02 progress 10/35; overall eligible progress 150/315

## Stage 3 Gold collection — operator_02/session_02 block 3

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_02.csv` (seed 20260922)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 15 total; 15 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 1, PAT 3, POKE 4, RUB 1, STATIC_TOUCH 3, STROKE 2, TAP 1
- Planned IDs: contiguous and unique from 000001 through 000015; all attempt numbers are 1
- Frames: 738–750; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.90, max 53.21 Hz
- Host poll rate: min 185.19, mean 186.69, max 188.21 Hz
- Signal range: -3 to 26
- Status: block passed; operator_02/session_02 progress 15/35; overall eligible progress 155/315

## Stage 3 Gold collection — operator_02/session_02 block 4

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_02.csv` (seed 20260922)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 20 total; 20 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 2, PAT 4, POKE 4, RUB 2, STATIC_TOUCH 4, STROKE 2, TAP 2
- Planned IDs: contiguous and unique from 000001 through 000020; all attempt numbers are 1
- Frames: 738–750; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.92, max 53.21 Hz
- Host poll rate: min 185.19, mean 186.59, max 188.21 Hz
- Signal range: -4 to 26
- Status: block passed; operator_02/session_02 progress 20/35; overall eligible progress 160/315

## Stage 3 Gold collection — operator_02/session_02 block 5

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_02.csv` (seed 20260922)
- Commands: standard five-trial block followed by `--max-new-trials 1` retry for planned 000021
- GPU: not used
- Session attempts: 26 total; 25 VALID Gold; 1 REDO; 0 UNCERTAIN
- REDO handling: planned 000021 STATIC_TOUCH attempt 1 remains REDO; attempt 2 is the sole Gold selection
- Session labels so far: IMPACT 2, PAT 5, POKE 4, RUB 3, STATIC_TOUCH 5, STROKE 3, TAP 3
- Planned IDs: 25 unique Gold selections from 000001 through 000025
- Frames: 738–750; all Gold matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.92, max 53.21 Hz
- Host poll rate: min 185.19, mean 186.66, max 188.21 Hz
- Signal range: -5 to 26
- Status: block passed; operator_02/session_02 progress 25/35; overall eligible progress 165/315

## Stage 3 Gold collection — operator_02/session_02 block 6

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_02.csv` (seed 20260922)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts cumulative: 31 total; 30 VALID Gold; 1 REDO; 0 UNCERTAIN
- Session labels so far: IMPACT 4, PAT 5, POKE 4, RUB 4, STATIC_TOUCH 5, STROKE 4, TAP 4
- Planned IDs: 30 unique Gold selections from 000001 through 000030
- Frames: 738–750; all Gold matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.92, max 53.21 Hz
- Host poll rate: min 185.19, mean 186.60, max 188.21 Hz
- Signal range: -5 to 27
- Status: block passed; operator_02/session_02 progress 30/35; overall eligible progress 170/315

## Stage 3 Gold collection — operator_02/session_02 complete

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_02.csv` (seed 20260922)
- Final command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Attempts: 36 total; 35 VALID Gold; 1 REDO; 0 UNCERTAIN
- Class balance: exactly 5 each for TAP, POKE, STATIC_TOUCH, STROKE, RUB, PAT, IMPACT
- Planned IDs: 35 unique Gold selections from 000001 through 000035
- REDO handling: planned 000021 attempt 1 remains REDO; attempt 2 is the sole Gold selection
- Frames: 738–750; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.92, max 53.21 Hz
- Host poll rate: min 185.19, mean 186.58, max 188.21 Hz
- Signal range: -5 to 27
- Known quality flag: SDK touch state false in every frame
- Status: session gate passed; operator_02 progress 70/105; overall eligible progress 175/315

## Stage 3 Gold collection — operator_02/session_03 start

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, new process/device initialization, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_03.csv` (seed 20260923)
- Command: `python scripts/record_session.py --operator-id operator_02 --session-id session_03 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- Collection timing note: started shortly after session_02 at the project owner's request; the preferred longer session break was not used
- Preflight: canonical manifest has 175 eligible rows; order file exists; target directory did not previously exist
- GPU: not used
- Status: first five trials ready to launch; no session_03 result claimed yet

## Stage 3 Gold collection — operator_02/session_03 block 1

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_03.csv` (seed 20260923)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 5 total; 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: PAT 1, POKE 1, RUB 2, STATIC_TOUCH 1
- Planned IDs: contiguous and unique from 000001 through 000005; all attempt numbers are 1
- Frames: 737–743; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.96, max 53.21 Hz
- Host poll rate: min 184.99, mean 185.88, max 186.50 Hz
- Signal range: -2 to 25
- Status: block passed; operator_02/session_03 progress 5/35; overall eligible progress 180/315

## Stage 3 Gold collection — operator_02/session_03 block 2

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_03.csv` (seed 20260923)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 10 total; 10 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 2, PAT 1, POKE 1, RUB 2, STATIC_TOUCH 1, STROKE 2, TAP 1
- Planned IDs: contiguous and unique from 000001 through 000010; all attempt numbers are 1
- Frames: 737–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.88, max 53.21 Hz
- Host poll rate: min 184.99, mean 186.34, max 187.50 Hz
- Signal range: -3 to 25
- Status: block passed; operator_02/session_03 progress 10/35; overall eligible progress 185/315

## Stage 3 Gold collection — operator_02/session_03 block 3

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_03.csv` (seed 20260923)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 15 total; 15 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 1, POKE 1, RUB 3, STATIC_TOUCH 2, STROKE 3, TAP 2
- Planned IDs: contiguous and unique from 000001 through 000015; all attempt numbers are 1
- Frames: 737–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.91, max 53.21 Hz
- Host poll rate: min 184.99, mean 186.58, max 187.50 Hz
- Signal range: -3 to 25
- Status: block passed; operator_02/session_03 progress 15/35; overall eligible progress 190/315

## Stage 3 Gold collection — operator_02/session_03 block 4

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_03.csv` (seed 20260923)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 20 total; 20 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 2, POKE 1, RUB 3, STATIC_TOUCH 4, STROKE 4, TAP 3
- Planned IDs: contiguous and unique from 000001 through 000020; all attempt numbers are 1
- Frames: 737–749; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.92, max 53.21 Hz
- Host poll rate: min 184.99, mean 186.72, max 187.95 Hz
- Signal range: -3 to 25
- Status: block passed; operator_02/session_03 progress 20/35; overall eligible progress 195/315

## Stage 3 Gold collection — operator_02/session_03 block 5

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_03.csv` (seed 20260923)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 25 total; 25 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 2, POKE 3, RUB 4, STATIC_TOUCH 4, STROKE 4, TAP 5
- Planned IDs: contiguous and unique from 000001 through 000025; all attempt numbers are 1
- Frames: 737–749; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.92, max 53.21 Hz
- Host poll rate: min 184.99, mean 186.69, max 187.95 Hz
- Signal range: -3 to 25
- Status: block passed; operator_02/session_03 progress 25/35; overall eligible progress 200/315

## Stage 3 Gold collection — operator_02/session_03 block 6

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_03.csv` (seed 20260923)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 30 total; 30 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 4, PAT 4, POKE 3, RUB 5, STATIC_TOUCH 5, STROKE 4, TAP 5
- Planned IDs: contiguous and unique from 000001 through 000030; all attempt numbers are 1
- Frames: 737–749; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.92, max 53.21 Hz
- Host poll rate: min 184.99, mean 186.72, max 188.00 Hz
- Signal range: -5 to 25
- Status: block passed; operator_02/session_03 progress 30/35; overall eligible progress 205/315

## Stage 3 Gold collection — operator_02/session_03 and operator_02 complete

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_02_session_03.csv` (seed 20260923)
- Final command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session_03 attempts: 35 total; 35 VALID Gold; 0 REDO/UNCERTAIN
- Session_03 class balance: exactly 5 each for TAP, POKE, STATIC_TOUCH, STROKE, RUB, PAT, IMPACT
- Operator_02 aggregate: 105 Gold across three sessions; exactly 15 per class
- All completed data: 210 Gold across six sessions; exactly 30 per class; operator_01 105 and operator_02 105
- Planned IDs: 35 unique Gold selections in every session
- Frames: 735–750; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.94, max 53.21 Hz
- Host poll rate: min 184.44, mean 186.77, max 188.25 Hz
- Signal range: -23 to 28
- Known quality flag: SDK touch state false in every frame
- Status: session_03 and operator_02 gates passed; overall eligible progress 210/315

## Stage 3 Gold collection — operator_03/session_01 start

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, new process/device initialization, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_01.csv` (seed 20261021)
- Command: `python scripts/record_session.py --operator-id operator_03 --session-id session_01 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- Participant gate: project owner confirmed a genuinely distinct operator_03 is prepared, trained, and understands the corrected pulse rule
- Preflight: canonical manifest has 210 eligible rows; order file exists; target directory did not previously exist
- GPU: not used
- Status: first five trials ready to launch; no operator_03 result claimed yet

## Stage 3 Gold collection — operator_03/session_01 block 1

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_01.csv` (seed 20261021)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 5 total; 5 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: PAT 2, POKE 1, STATIC_TOUCH 1, STROKE 1
- Planned IDs: contiguous and unique from 000001 through 000005; all attempt numbers are 1
- Frames: 742–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.71, mean 52.96, max 53.21 Hz
- Host poll rate: min 186.24, mean 186.85, max 187.50 Hz
- Signal range: -3 to 23
- Status: block passed; operator_03/session_01 progress 5/35; overall eligible progress 215/315

## Stage 3 Gold collection — operator_03/session_01 block 2

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_01.csv` (seed 20261021)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 10 total; 10 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: PAT 2, POKE 2, RUB 2, STATIC_TOUCH 2, STROKE 1, TAP 1
- Planned IDs: contiguous and unique from 000001 through 000010; all attempt numbers are 1
- Frames: 741–747; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.93, max 53.21 Hz
- Host poll rate: min 185.99, mean 186.81, max 187.50 Hz
- Signal range: -4 to 23
- Status: block passed; operator_03/session_01 progress 10/35; overall eligible progress 220/315

## Stage 3 Gold collection — operator_03/session_01 block 3

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_01.csv` (seed 20261021)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 15 total; 15 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 1, PAT 2, POKE 4, RUB 2, STATIC_TOUCH 2, STROKE 1, TAP 3
- Planned IDs: contiguous and unique from 000001 through 000015; all attempt numbers are 1
- Frames: 741–749; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.99, max 53.21 Hz
- Host poll rate: min 185.99, mean 187.05, max 188.00 Hz
- Signal range: -4 to 24
- Status: block passed; operator_03/session_01 progress 15/35; overall eligible progress 225/315

## Stage 3 Gold collection — operator_03/session_01 block 4

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_01.csv` (seed 20261021)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 20 total; 20 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 2, PAT 2, POKE 4, RUB 3, STATIC_TOUCH 4, STROKE 2, TAP 3
- Planned IDs: contiguous and unique from 000001 through 000020; all attempt numbers are 1
- Frames: 738–749; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 53.00, max 53.21 Hz
- Host poll rate: min 185.24, mean 186.97, max 188.00 Hz
- Signal range: -4 to 24
- Status: block passed; operator_03/session_01 progress 20/35; overall eligible progress 230/315

## Stage 3 Gold collection — operator_03/session_01 block 5

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_01.csv` (seed 20261021)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 25 total; 25 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 3, PAT 4, POKE 4, RUB 4, STATIC_TOUCH 4, STROKE 2, TAP 4
- Planned IDs: contiguous and unique from 000001 through 000025; all attempt numbers are 1
- Frames: 738–749; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.98, max 53.21 Hz
- Host poll rate: min 185.24, mean 187.03, max 188.00 Hz
- Signal range: -4 to 24
- Status: block passed; operator_03/session_01 progress 25/35; overall eligible progress 235/315

## Stage 3 Gold collection — operator_03/session_01 block 6

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_01.csv` (seed 20261021)
- Command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Session attempts: 30 total; 30 VALID Gold; 0 REDO/UNCERTAIN
- Session labels so far: IMPACT 5, PAT 5, POKE 4, RUB 5, STATIC_TOUCH 4, STROKE 3, TAP 4
- Planned IDs: contiguous and unique from 000001 through 000030; all attempt numbers are 1
- Frames: 738–751; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.98, max 53.21 Hz
- Host poll rate: min 185.24, mean 187.07, max 188.46 Hz
- Signal range: -4 to 25
- Status: block passed; operator_03/session_01 progress 30/35; overall eligible progress 240/315

## Stage 3 Gold collection — operator_03/session_01 complete

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Config: corrected pulse instructions, real SDK, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_01.csv` (seed 20261021)
- Final command: standard session runner with `--max-new-trials 5`
- GPU: not used
- Attempts: 35 total; 35 VALID Gold; 0 REDO/UNCERTAIN
- Class balance: exactly 5 each for TAP, POKE, STATIC_TOUCH, STROKE, RUB, PAT, IMPACT
- Planned IDs: contiguous and unique from 000001 through 000035
- Frames: 738–751; all matrices finite and shaped `[T,18,29]`
- Observed matrix update rate: min 52.70, mean 52.98, max 53.21 Hz
- Host poll rate: min 185.24, mean 187.04, max 188.46 Hz
- Signal range: -4 to 25
- Known quality flag: SDK touch state false in every frame
- Status: session gate passed; operator_03 progress 35/105; overall eligible progress 245/315

## Stage 3 Gold collection — operator_03/session_02 start

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Config: corrected pulse instructions, real SDK, new process/device initialization, 4-second capture, 5 ms host poll interval, 3-second countdown
- Seed/order: `operator_03_session_02.csv` (seed 20261022)
- Command: `python scripts/record_session.py --operator-id operator_03 --session-id session_02 --duration-s 4 --poll-interval-ms 5 --countdown-s 3 --max-new-trials 5`
- Collection timing note: started shortly after session_01 at the project owner's request; the preferred longer session break was not used
- Preflight: canonical manifest has 245 eligible rows; order file exists; target directory did not previously exist
- GPU: not used
- Status: first five trials ready to launch; no session_02 result claimed yet
