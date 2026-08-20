# Experiment Ledger

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
