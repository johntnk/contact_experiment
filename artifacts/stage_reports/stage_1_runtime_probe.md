# Stage 1 Runtime Probe Report

- Date: 2026-08-20
- Branch: `stage-1-sdk-probe`
- GPU used: no (not required for SDK acquisition)
- Result: passed

## Completed checks

- Added an isolated `ctypes` wrapper with explicit API signatures and guaranteed
  disable/release cleanup.
- Added a short probe for matrix dimensions, host poll/update rates, duplicate
  reads, timing statistics, value/noise statistics, touch ratio, current JSON,
  and optional four-corner orientation capture.
- Added four standard-library unit tests covering lifecycle, matrix reads,
  initialization errors, invalid call order, and cleanup after exceptions.
- Python compilation, all four tests, CLI help, and `git diff --check` passed.

## Hardware evidence and root cause

The initial command failed before acquisition:

```powershell
python scripts\probe_sdk.py --duration-s 5 --poll-interval-ms 5 --output artifacts\stage_reports\stage_1_probe_smoke.json
```

SDK error:

```text
deepskin_init failed with code -1: Device not found or open failed
```

The vendor's unchanged `DeepskinSDK_TestPython/read_gesture.py` initially produced
the same error. A detailed scan found Deepskin as `USB\VID_0EEF&PID_C002`, bus-reported as
`eGalaxTouch P81X32 A0KZ v00_T0 k4.18.203`, started without a Windows device
error. An unplug/rescan comparison confirmed its identity: this device and its
four HID children disappeared when only Deepskin was removed, while the keyboard,
mouse, and motherboard HID devices stayed connected.

The supplier Tool and the x64 C++ `test_matrix.exe` both acquired live matrices.
Hash comparison then found that `DeepskinSDK_TestPython/DeepskinSDK.dll` differs
from the working x64 distribution DLL. A second issue was that the SDK internally
resolves `HIDdAPI.dll` relative to the process working directory during
`deepskin_init()`. The wrapper now selects the working x64 DLL and temporarily
switches to its directory for initialization, under a process-wide lock, before
restoring the original directory.

Two successful artifacts were produced:

- `stage_1_probe_smoke.json`: 5 seconds, 922 polls, 18x29 matrix, 52.2 Hz
  host-observed matrix change rate.
- `stage_1_probe_root_smoke.json`: 3 seconds from the repository root, 552 polls,
  18x29 matrix, 52.33 Hz host-observed matrix change rate.

Neither initial run included a detected touch, so those artifacts establish idle
acquisition and timing. The final `stage_1_probe.json` additionally captures all
four physical corners:

- top-left: `(0.186, 0.330)`
- top-right: `(0.838, 0.301)`
- bottom-right: `(0.852, 0.700)`
- bottom-left: `(0.144, 0.720)`

Left/right and top/bottom order are consistent with the row-major matrix as
reported. No transpose or axis inversion is required.

## Gate status

Passed. Implementation, offline tests, supplier Tool, x64 C++ test, Python
hardware acquisition, and manual four-corner orientation all succeeded.
