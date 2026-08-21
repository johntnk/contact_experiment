# Known Errors

## 2026-08-21 — pulse_count instruction was operationally ambiguous

- Date: 2026-08-21
- Context: Stage 3 controlled collection after operator_01 completion and during operator_02/session_01.
- Symptom: The project owner reported that previously recorded trials with `pulse_count` were executed using the wrong interpretation of `nearby pulses`.
- Root cause: The session UI displayed only a number and the phrase `nearby pulses`; it did not require separated contacts, full lift-off, a nearby 1–2 cm position change, or prohibit sliding/repeated pressure in place. The runner also skipped existing Gold and the manifest had no replacement-attempt policy.
- Fix: Added an auditable minimum-attempt recollection plan, recorder plan mode, explicit pulse instructions, and manifest filtering that excludes superseded attempts while preserving immutable raw data.
- Verification evidence: The focused replacement test and all 13 unit tests passed. A candidate manifest excluded all 39 affected prior Gold attempts and contained 95 currently eligible rows.
- Future caution: Every numeric protocol field needs an operational definition visible before countdown. Never rely on a short note such as `nearby pulses`, and never re-record a VALID trial without an explicit manifest supersession rule.
- Related files/commands: `protocol/recollection_plans/pulse_count_v1.csv`, `src/deepskin_data/recollection.py`, `scripts/record_session.py`, `src/deepskin_data/manifest.py`, `python -m unittest discover -s tests -v`.

## 2026-08-20 — Python SDK reports device not found while vendor tools work

- Date: 2026-08-20
- Context: Stage 1 Deepskin runtime probe on Windows 11, 64-bit Python, sensor
  `USB\VID_0EEF&PID_C002` (`eGalaxTouch P81X32 A0KZ v00_T0 k4.18.203`).
- Symptom: `deepskin_init()` returned `-1` / `Device not found or open failed`
  from Python, although the supplier Tool and x64 C++ matrix test worked.
- Root cause: `DeepskinSDK_TestPython/DeepskinSDK.dll` differed from the working
  x64 distribution DLL. In addition, the working SDK internally resolved
  `HIDdAPI.dll` relative to the process working directory during initialization.
  Loading `DeepskinSDK.dll` by absolute path was insufficient.
- Fix: Default to `DeepskinSDK_Distribution_cpp_x64/bin/DeepskinSDK.dll`; load it
  with `LOAD_WITH_ALTERED_SEARCH_PATH`; serialize `deepskin_init()` and temporarily
  change the process working directory to the DLL directory, restoring it in a
  `finally` block.
- Verification evidence: Vendor x64 `test_matrix.exe` acquired data; Python probe
  then succeeded from both the DLL directory and repository root. Final probe
  reported an 18x29 matrix, about 52.33 Hz host-observed matrix changes, and four
  physically consistent corner centroids.
- Future caution: Do not assume identically named SDK DLLs in different supplier
  folders are interchangeable. Hash them, keep each dependent DLL beside its
  matching SDK, and remember that changing cwd is process-global even when
  serialized.
- Related files/commands: `src/deepskin_runtime/sdk.py`, `scripts/probe_sdk.py`,
  `artifacts/stage_reports/stage_1_probe.json`, `Get-FileHash`,
  `python scripts\probe_sdk.py --orientation`.

## 2026-08-20 — Recorder confused host poll rate with observed matrix update rate

- Date: 2026-08-20
- Context: Stage 2 hardware acceptance trial and Gold manifest audit.
- Symptom: The first accepted trial reported `sampling_rate_observed_hz=185.99`,
  while replay showed only 156 changed transitions in about 2.984 seconds.
- Root cause: Metadata divided all host polls by duration instead of counting the
  first matrix plus changed-matrix transitions, violating frozen decision D-002.
- Fix: Store changed-matrix rate as `sampling_rate_observed_hz`, store poll rate
  separately as `host_poll_rate_hz`, and exclude legacy Gold candidates lacking
  the explicit poll-rate field. Flag trials where the SDK touch flag is always
  false instead of silently treating that flag as reliable contact evidence.
- Verification evidence: `trial_000006` replayed as `[553,18,29]` with 156
  changed transitions; metadata reports 52.61 Hz observed updates and 185.32 Hz
  host polls. The final acceptance manifest contains only this corrected trial.
- Future caution: Define every rate by its numerator before publishing it. Do
  not infer hardware sampling or drop counts from polling, and do not use this
  device's SDK touch boolean as the sole contact detector.
- Related files/commands: `src/deepskin_data/recorder.py`,
  `src/deepskin_data/manifest.py`, `scripts/replay_trial.py`,
  `python scripts\build_gold_manifest.py`.

## 2026-08-20 — Controlled VALID trial allowed a mismatched verified label

- Date: 2026-08-20
- Context: Stage 3 simulated session-runner smoke test.
- Symptom: A planned `RUB` trial could be confirmed as `VALID` with verified
  label `TAP` and enter the Gold manifest.
- Root cause: The schema checked that both labels belonged to the seven-class
  vocabulary but did not enforce equality for a controlled valid execution.
- Fix: `VALID` now requires `verified_label == instruction_label`; both Recorder
  prompts reject mismatches and direct the operator to REDO or UNCERTAIN.
- Verification evidence: Focused mismatch regression and all 12 tests passed. A
  corrected simulated `RUB -> RUB` session trial was recorded, replayed, and
  included with its planned trial ID in a one-row manifest.
- Future caution: Vocabulary validity is weaker than protocol validity. Enforce
  relationships between fields at the schema layer, not only in interactive UI.
- Related files/commands: `src/deepskin_data/schema.py`,
  `scripts/record_trial.py`, `scripts/record_session.py`,
  `tests/test_trial_data.py`.

## 2026-08-21 — live STROKE prompt described RUB behavior
- Date: 2026-08-21
- Context: first controlled live inference smoke using `scripts/recognize_live.py` and the final seven-class model
- Symptom: expected `STROKE`, predicted `RUB`; RUB decision score 6.301, STROKE ranked third at 4.263
- Root cause: the operator-facing instruction said to perform continuous/back-and-forth stroking for the four-second window. The versioned protocol defines STROKE as a single directional path and RUB as one or more return cycles, so the prompt described the wrong class behavior.
- Fix: added explicit per-class live instructions; STROKE now requires one left-to-right path followed by full lift-off and explicitly prohibits return rubbing.
- Verification evidence: the failed result is preserved at `artifacts/live_validation/live_smoke_stage6_01.json`; its model hash matches the packaged model, matrix is finite `[743,18,29]`, and host poll rate is 186.45 Hz. After the prompt fix, `live_smoke_stage6_02.json` predicted STROKE as Top-1 (score 6.305) on a corrected single-direction stroke with the same valid shape and 186.45 Hz host poll rate; 15 tests passed.
- Future caution: never use informal words such as continuous stroke or back-and-forth for STROKE; live prompts must preserve the versioned gesture schedule's direction and return-cycle semantics.
- Related files/commands: `protocol/gesture_variation_schedule.csv`, `scripts/recognize_live.py`, `python scripts/recognize_live.py --expected-label STROKE ...`

## 2026-08-21 — live validation saved summaries without raw matrices
- Date: 2026-08-21
- Context: seven-class live inference smoke after the final offline model package
- Symptom: the suite produced complete predictions and matrix summary statistics, but a 3/7 result could not be inspected for event onset, duration, area evolution, or TAP/POKE waveform differences because no raw capture files existed.
- Root cause: `scripts/recognize_live.py` wrote only JSON summary fields and discarded the arrays returned by `collect_frames` after feature extraction.
- Fix: every future live JSON now has a same-stem compressed NPZ containing matrix, timestamps, frame IDs, and touch state; JSON records the raw filename and SHA-256, and overwrite protection covers both files.
- Verification evidence: the original suite contains seven JSON files and zero NPZ files, reproducing the diagnostic gap. After the patch, `tap_poke_diagnostic_01_tap.json` and its same-stem NPZ were both created; recorded and computed NPZ SHA-256 values match, arrays are finite `[740,18,29]`, and all four required array keys are present. Syntax checks and 15 tests passed.
- Future caution: all live validation used for segmentation or error analysis must preserve immutable raw arrays; summary-only files are adequate for plumbing checks but not model diagnosis.
- Related files/commands: `scripts/recognize_live.py`, `artifacts/live_validation/seven_class_smoke_01/`, `python scripts/recognize_live.py --expected-label ... --output ...`
