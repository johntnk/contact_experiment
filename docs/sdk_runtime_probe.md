# Stage 1: SDK Runtime Probe

## Purpose

`scripts/probe_sdk.py` performs a short, read-only runtime check through the public
64-bit Deepskin SDK. It records host-observed behavior; it does not claim access
to firmware timestamps, sequence numbers, or hardware drop counters.

## Prerequisites

- Windows 10/11, 64-bit Python.
- Deepskin connected by USB and visible to Windows as a HID device.
- No vendor demo, matrix viewer, or other process currently holding the device.
- The x64 distribution's `bin/DeepskinSDK.dll` and `HIDdAPI.dll` kept together.

Do not use the similarly named DLL in `DeepskinSDK_TestPython`: its binary hash
differs from the x64 DLL that successfully drives this hardware.

The probe itself uses only the Python standard library. NumPy is not required.

The vendor DLL performs an internal relative lookup for `HIDdAPI.dll` during
`deepskin_init()`. The wrapper temporarily and safely changes the process working
directory to the selected DLL directory for that call, then restores it.

## Commands

Run a five-second smoke test:

```powershell
python scripts\probe_sdk.py `
  --duration-s 5 `
  --poll-interval-ms 5 `
  --output artifacts\stage_reports\stage_1_probe_smoke.json
```

After the smoke test passes, run the four-corner orientation check:

```powershell
python scripts\probe_sdk.py `
  --duration-s 10 `
  --poll-interval-ms 5 `
  --orientation `
  --output artifacts\stage_reports\stage_1_probe.json
```

Follow the prompts and press one corner at a time. The output file is created
only after the entire run succeeds. Existing output files are never overwritten.

## Output interpretation

- `poll_rate_hz`: rate at which the host called the SDK.
- `changed_matrix_rate_hz`: matrices per second whose values differed from the
  preceding host read. This is an observation, not a guaranteed device sampling
  frequency.
- `duplicate_reads`: consecutive reads with identical matrix values.
- `hardware_drop_count`: always `null`; the public SDK exposes no frame sequence
  number or device timestamp from which to compute it.
- `orientation`: pressure-weighted centroids recorded for the four prompted
  corners. These measurements are used to confirm or correct matrix orientation.

## Current hardware result (2026-08-20)

Both the new probe and the vendor's unmodified `read_gesture.py` fail at
`deepskin_init()` with `Device not found or open failed`. A detailed USB scan
does show the sensor as `USB\VID_0EEF&PID_C002`, reported by the bus
as `eGalaxTouch P81X32 A0KZ v00_T0 k4.18.203`. It is started with no Windows
device error. The bundled HID library also contains the vendor ID `0EEF`, but
that fact alone does not prove SDK compatibility with product ID `C002`.

This localizes the current blocker to SDK/HID device selection or opening rather
than the new Python wrapper. Device identity was confirmed by an unplug/rescan
comparison: `0EEF:C002` and all four of its HID child interfaces disappeared
when only Deepskin was unplugged, while the keyboard, mouse, and motherboard HID
devices remained present.

Reconnect or power-cycle Deepskin, test the vendor Tool's `register` then
`enable` workflow, close the Tool so it releases the HID device, and rerun the
vendor Python example.
Once that initializes, rerun the two probe commands above.
