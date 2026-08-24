# Stage 21 — PAT streaming parameter tuning

- Date: 2026-08-21
- Scope: event-boundary defaults only; no retraining and no raw-data mutation
- Dataset: 315 Gold trials from the packaged training manifest
- Model evidence: strict LOPO PAT F1 `0.9149`; 43/45 PAT trials correct, with two confused as IMPACT
- PAT execution evidence: every PAT trial contained 2–4 active runs (18 with 2, 19 with 3, 8 with 4)
- PAT inactive gaps: median `312.5 ms`, P75 `391.0 ms`, P90 `500.0 ms`, 41/80 gaps exceeded the old `300 ms` hold
- PAT active-run duration: median `375 ms`; no run was under the `40 ms` start debounce

## Decision

- Keep start threshold `3.0` and baseline margin `2.0` because they match training segmentation.
- Keep start debounce `40 ms` because it does not truncate the observed PAT pulses.
- Increase end hold from `300 ms` to `550 ms`, covering the PAT gap P90 plus roughly one observed device-update interval.
- Keep selected positive-gate multiplier `1.20`.
- Correct the PAT operator prompt from one pat to 2–4 separated pats.

The new hold adds about 250 ms of output latency. It may combine deliberately separate gestures performed less than 550 ms apart; this is the explicit tradeoff for better PAT episode aggregation. Live PAT validation is still required.
