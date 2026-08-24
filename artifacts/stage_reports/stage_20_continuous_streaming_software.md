# Stage 20 — Continuous streaming software implementation

- Date: 2026-08-21
- Status: software implementation and offline verification passed; hardware endurance validation pending
- Runtime: SDK remains enabled inside one continuous acquisition loop
- Event detector: adaptive idle baseline, 40 ms start debounce, 300 ms end hold, 150 ms pre-roll, 8 s maximum event
- Public output: accepted final target gestures only
- Rejection behavior: internal `SUPPRESSED_LOW_CONFIDENCE` diagnostic on stderr; no public `UNKNOWN` gesture
- Gate control: calibrated per-class base thresholds plus a runtime threshold multiplier; selected runtime default `1.2`
- GUI: continuous start/stop, detector parameters, gate multiplier, candidate class, distance, base/effective thresholds, acceptance state
- Raw event persistence: disabled by default

## Verification

- Python syntax compilation: passed
- Unit tests: 25/25 passed
- Added coverage: event debouncing/aggregation/max duration and gate-threshold multiplier
- Model-package replay: `operator_01/session_01/trial_000001_attempt_03`
- Replay result: `RUB`, accepted; distance `0.0`, calibrated threshold `3.668354083052745`

The replay verifies software compatibility but is not a substitute for a live USB run. The next gate is a controlled live stream followed by a longer start/stop stability check.
