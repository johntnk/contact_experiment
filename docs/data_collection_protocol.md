# Deepskin V1 Controlled Data Collection Protocol

## Scope

Stage 2 records one immutable 18x29 trial at a time. The seven allowed labels are
`TAP`, `POKE`, `STATIC_TOUCH`, `STROKE`, `RUB`, `PAT`, and `IMPACT`.
`NO_CONTACT` and `UNKNOWN` are not training classes.

### TAP versus POKE operational boundary

- `TAP`: one fast contact, target active duration approximately 100–300 ms, followed by immediate full lift-off; do not deliberately press inward or dwell.
- `POKE`: one fingertip inward press with a short dwell, target active duration approximately 500–1500 ms, followed by full lift-off; do not perform it as a quick light tap.
- Intensity remains an independent instruction and must not be used alone to decide TAP versus POKE.
- Duration is a protocol aid and audit flag, not an automatic ground-truth relabeling rule.

## Session preparation

1. Use a new `session_id`, restart the acquisition process, and collect a fresh
   idle baseline.
2. Generate the 35-trial order with a recorded seed:

```powershell
python scripts\generate_session_order.py `
  --operator-id operator_01 `
  --session-id session_01 `
  --seed 20260820
```

The generator includes each class five times and rejects runs longer than two
identical labels. Existing order files are never overwritten.

## Recording one trial

### pulse_count operational rule

- `pulse_count=N` means N separated short contacts.
- Fully lift after every contact before making the next one.
- Place the next contact nearby, approximately 1–2 cm from the previous position, rather than exactly overlapping it.
- A pulse is not a sustained press, repeated pressure without lift-off, or a sliding motion; mark those executions `REDO`.
- When pulse_count is shown, the operator must restate this rule before starting the countdown.

Use the row in the generated order as the instruction source. Example:

```powershell
python scripts\record_trial.py `
  --operator-id operator_01 `
  --session-id session_01 `
  --trial-id trial_000001 `
  --instruction-label STROKE `
  --duration-s 5 `
  --speed SLOW `
  --direction LEFT_TO_RIGHT `
  --position CENTER
```

After recording, an operator must select exactly one status:

- `VALID`: explicitly enter one of the seven verified labels and type `YES`.
  The record is marked `CONTROLLED_CONFIRMED` and `GOLD`.
- `REDO`: execution was wrong; `verified_label` remains null.
- `UNCERTAIN`: execution cannot be confidently verified; `verified_label`
  remains null.

The instruction is never copied automatically into the verified label.
For a controlled `VALID` trial, the explicitly entered verified label must match
the instruction label. If the performed gesture belongs to another class, mark
the attempt `REDO` or `UNCERTAIN`; do not relabel it as valid.

For a full or resumed 35-trial session, use:

```powershell
python scripts\record_session.py `
  --operator-id operator_01 `
  --session-id session_01
```

The session runner initializes the device once, follows the frozen order, skips
already completed Gold trials, and writes retries as `_attempt_02`, etc. Use
`--max-new-trials N` for a safe partial collection block.

## Trial files and safety

Each trial contains `matrix.npz`, `metadata.json`, and `sdk_events.jsonl` under
`data/raw/deepskin/<operator>/<session>/<trial>/`. The recorder writes and
validates a private temporary directory, then publishes it by atomic rename.
Any existing trial directory causes an immediate failure; raw trials are never
overwritten.

`matrix.npz` contains `matrix [T,18,29]`, host-monotonic `timestamps_ms [T]`,
contiguous host-generated `frame_ids [T]`, and SDK `touch_state [T]`. The SDK
does not expose hardware timestamps or sequence numbers, so exact hardware drop
counts must not be claimed. `sampling_rate_observed_hz` is calculated from the
first matrix plus changed-matrix transitions; the faster host polling rate is
stored separately as `host_poll_rate_hz`. A `VALID` record missing the latter is
treated as a legacy metric record and is excluded from the Gold manifest.

## Manifest and replay validation

Build the manifest after recording:

```powershell
python scripts\build_gold_manifest.py
```

Every candidate trial is reopened and validated. Only `VALID` records with
`label_quality=GOLD` enter `gold_manifest.csv`; `REDO` and `UNCERTAIN` remain in
raw storage for audit but are excluded from training.

Validate and summarize any one trial without changing it:

```powershell
python scripts\replay_trial.py data\raw\deepskin\operator_01\session_01\trial_000001
```
