# Known Errors

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
