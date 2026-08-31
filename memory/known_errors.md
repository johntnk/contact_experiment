# Known Errors

## 2026-08-24 - complete-event TCN degraded on incomplete causal windows

- Date: 2026-08-24
- Context: continuous recognition reused the formal personalized TCN on a rolling partial-event window.
- Symptom: the operator reported weaker IMPACT, TAP, and POKE recognition, while PAT could be emitted as STROKE.
- Root cause: the TCN was trained on complete events. Runtime resampled an unfinished event prefix to the model's full temporal length, creating a distribution shift; debounce changes only output timing and cannot reconstruct missing future evidence.
- Fix: route sustained RUB/STATIC_TOUCH/STROKE through causal sliding-window inference, but classify TAP/POKE/IMPACT/PAT only from the completed event after release. Preserve the pure sliding-window implementation as a rollback entry.
- Verification evidence: Python compilation and the full 37-test suite pass, including an explicit seven-class routing regression. The complete-event path classified all 28 detector-complete PAT/RUB development captures correctly; two recordings lacked a detector-complete event and were excluded.
- Future caution: do not claim true early recognition from a model trained only on complete events. Train with prefix/window augmentation or a framewise objective before moving transient labels back to the causal path.
- Related files/commands: `scripts/realtime_stream_gui.py`, `scripts/realtime_stream_gui_v1.py`, `src/deepskin_temporal/realtime.py`, `tests/test_realtime_temporal.py`, `artifacts/evaluation/hybrid_event_path_pat_rub_20260824.json`.

## 2026-08-24 - generic realtime debounce suppressed short IMPACT events

- Date: 2026-08-24
- Context: causal 100 ms sliding-window recognition with a 200 ms minimum evidence delay and three generic first-label confirmations.
- Symptom: the operator reported that IMPACT recognition became noticeably worse in the realtime streaming version.
- Root cause: IMPACT is brief, but it inherited the same three-confirmation startup gate as sustained gestures. Nineteen of 45 Gold IMPACT captures had fewer than three active inference opportunities after the evidence delay, so even perfect frame-level predictions could not be emitted before release.
- Fix: use two first-label confirmations for IMPACT while retaining three for generic classes and two for all later label switches; expose the IMPACT confirmation count in the GUI.
- Verification evidence: the opportunity audit improves theoretical coverage from 26/45 to 44/45 Gold IMPACT captures; a 30-capture PAT/RUB development replay introduced zero false first IMPACT outputs and preserved its previous final-label result; full tests passed after the change.
- Future caution: compare each gesture's active-duration distribution with the complete runtime confirmation budget. Short transient and sustained gestures should not automatically share identical startup debounce.
- Related files/commands: `scripts/realtime_stream_gui.py`, `scripts/audit_realtime_replay.py`, `src/deepskin_temporal/realtime.py`, `artifacts/evaluation/realtime_stream_replay_pat_impact_fast_hold300_20260824.json`.

## 2026-08-24 - inference monitoring added redundant CUDA barriers to the sampling thread

- Date: 2026-08-24
- Context: first live use after adding end-to-end inference timing to the causal streaming GUI.
- Symptom: the operator reported that recognition felt worse even though the model, thresholds, window, and debounce parameters were unchanged.
- Root cause: timing instrumentation called `torch.cuda.synchronize()` before and after every inference on the same worker that reads the SDK. The subsequent `.cpu().numpy()` already waits for CUDA completion, so the explicit barriers were redundant and added avoidable sampling-thread stalls.
- Fix: remove both explicit CUDA synchronization calls and measure from before feature extraction through the existing CPU result transfer. Keep the bounded timing history and GUI metrics unchanged.
- Verification evidence: process inspection showed one active GUI interpreter pair rather than competing high-load GUI instances; the focused five-test realtime suite and full 36-test suite passed; no explicit synchronize call remains in the GUI.
- Future caution: observability must not add synchronization barriers to hardware acquisition paths. Prefer existing completion points, or move profiling to a separate path if more precise device-only timing is required.
- Related files/commands: `scripts/realtime_stream_gui.py`, `src/deepskin_temporal/realtime.py`, `tests/test_realtime_temporal.py`, `python -m unittest discover -s tests -q`.

## 2026-08-24 - motion-channel TCN improved Gold OOF but worsened live PAT/RUB

- Date: 2026-08-24
- Context: exploratory attempt to correct operator-reported PAT/RUB confusion in the continuous TCN GUI.
- Symptom: adding explicit contact, pressure-change, and centroid-motion channels raised pooled Gold LOPO Macro F1 from 0.8623 to 0.8888, but accuracy on eight complete live diagnostics fell from 2/8 to 1/8; four of five PAT captures became RUB.
- Root cause: the new live PAT captures did not match the frozen Gold PAT protocol. All five were one continuous active run at the 100 ms contact-gap definition, and only one separated into multiple runs even at 20-40 ms. The motion channels amplified this continuous-contact domain shift instead of restoring repeated-pat semantics.
- Fix: reject the motion-v2 package for GUI deployment, preserve the old TCN runtime, and require a separate natural-use PAT/RUB adaptation dataset before another model iteration.
- Verification evidence: three Gold outer folds produced Macro F1 0.875650/0.894284/0.895428 with zero PAT/RUB cross-confusions; exact runtime replay excluded two RUB captures lacking the 550 ms release tail and measured motion-v2 at 1/8 on the remaining immutable raw files. All 31 unit tests passed.
- Future caution: do not select temporal channels or runtime models solely from the original separated-pulse Gold protocol when intended users perform PAT as residual/continuous capacitive contact. Offline gain and live behavior must both pass, and already-inspected live diagnostics are development data thereafter.
- Related files/commands: `src/deepskin_temporal/sequence.py`, `scripts/audit_live_pat_rub_tcn.py`, `scripts/train_temporal_tcn.py`, `scripts/run_temporal_outer_fold.py`, `scripts/train_temporal_final.py`, `artifacts/evaluation/pat_rub_live_tcn_motion_v2_audit_20260824.json`.

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

## 2026-08-21 — continuous GUI crashed on an event without a valid touch segment

- Date: 2026-08-21
- Context: continuous Deepskin GUI displaying a completed event rejected as `no_touch_event`.
- Symptom: Tkinter callback raised `TypeError: unsupported format string passed to NoneType.__format__` and stopped updating results.
- Root cause: `_show_result` formatted optional gate values with `:.2f`; `apply_positive_gate` intentionally returns `None` for distance and threshold when event segmentation finds no valid touch.
- Fix: added a shared optional-metric formatter, rendered missing metrics as `—`, and added a specific ignored-event explanation for `no_touch_event`.
- Verification evidence: focused nullable-metric regression passed; Python compilation passed; full suite passed 26/26.
- Future caution: treat diagnostic result fields as nullable at every UI/output boundary and test rejection/error payloads, not only accepted predictions.
- Related files/commands: `scripts/stream_recognize_gui.py`, `tests/test_stream_gui.py`, `python -m unittest tests.test_stream_gui -v`, `python -m unittest discover -s tests -q`.

## 2026-08-21 — continuous PAT episodes were reduced to one IMPACT-like contact

- Date: 2026-08-21
- Context: continuous social-touch recognition after increasing the episode end hold for PAT.
- Symptom: an operator's 2–4-contact PAT repeatedly appeared as IMPACT in the GUI.
- Root cause: `ContactEventDetector` preserved the complete episode, but `classify_event` subsequently called longest-run segmentation, so repeated-contact evidence was unavailable to the final label decision.
- Fix: count micro-contacts on the complete episode before segmentation and apply the protocol's repeated-impulse PAT rule only to an IMPACT candidate with 2–4 separated, non-trivial contacts; expose the correction in the GUI.
- Verification evidence: focused regression passed; full suite passed 27/27; 315-row full-fit Gold replay fired zero corrections and changed no stored IMPACT event.
- Future caution: episode-level gesture semantics must be computed before any operation that selects a single micro-contact. Treat full-fit replay only as a safety check, not a generalization score.
- Related files/commands: `src/deepskin_data/streaming.py`, `scripts/stream_recognize.py`, `scripts/stream_recognize_gui.py`, `tests/test_training.py`, `artifacts/stage_reports/stage_22_pat_episode_runtime_fix.md`.

## 2026-08-21 — PAT episode correction was suppressed by the wrong gate reference

- Date: 2026-08-21
- Context: first live attempt after adding IMPACT-to-PAT episode correction.
- Symptom: PAT stopped producing a recognized result.
- Root cause: after relabeling an IMPACT candidate as PAT, the code compared its single-contact feature vector with PAT gate references; additionally, the streaming segmenter's 200 ms baseline window could include the long first contact despite only 150 ms pre-roll, producing `no_touch_event`.
- Fix: gate the original IMPACT model evidence before exposing the episode-corrected PAT label, and use a 75 ms baseline window only for streaming events while preserving the 200 ms offline-training default.
- Verification evidence: two focused regressions passed; syntax checks passed; full suite passed 28/28.
- Future caution: semantic post-processing must not silently change the statistical reference used to validate upstream evidence. A streaming baseline window must fit completely inside guaranteed idle pre-roll.
- Related files/commands: `scripts/stream_recognize.py`, `src/deepskin_data/training.py`, `tests/test_training.py`, `python -m unittest discover -s tests -q`.

## 2026-08-24 — temporal loader rejected every Gold trial because timestamps repeat

- Date: 2026-08-24
- Context: first V2 TCN GPU smoke on the existing Deepskin Gold recordings.
- Symptom: sequence extraction stopped before training with `temporal trial must be finite with strictly increasing timestamps`.
- Root cause: all 315 recordings contain non-decreasing millisecond-quantized timestamps with repeated values; host polling produces multiple observations in the same timestamp bin, although no timestamp decreases.
- Fix: accept non-decreasing timestamps and deterministically retain the final observation for each duplicate timestamp before interpolation; continue to reject actual decreases.
- Verification evidence: all 315 trials were audited (duplicates present, zero decreases); two focused tests passed; full suite passed 30/30; the two-epoch CUDA smoke then completed with finite loss and gradients.
- Future caution: define whether a time-series algorithm requires monotonic or strictly monotonic time. Normalize legitimate duplicate timestamp bins before interpolation rather than invalidating Gold data.
- Related files/commands: `src/deepskin_temporal/sequence.py`, `tests/test_temporal_sequence.py`, `scripts/train_temporal_tcn.py`, `artifacts/temporal/tcn_smoke_v1/report.json`.
