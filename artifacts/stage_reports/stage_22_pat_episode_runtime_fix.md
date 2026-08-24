# Stage 22 — PAT episode runtime fix

- Date: 2026-08-21
- Symptom: repeated PAT actions were consistently emitted as IMPACT in the continuous GUI
- Root cause: the online detector aggregated nearby contacts, but the downstream training-compatible segmenter retained only the longest active run, discarding PAT's repeated-contact evidence before final labeling
- Fix: count non-trivial micro-contacts on the complete online episode before longest-run segmentation; when the model candidate is IMPACT and the episode contains 2–4 contacts separated by at least 100 ms, apply the frozen repeated-impulse definition and label the episode PAT
- Bounce protection: contacts shorter than 40 ms are ignored and gaps shorter than 100 ms are bridged
- GUI: displays model candidate, PAT episode correction, and effective pulse count
- Gate ordering: validate the original IMPACT model evidence first, then expose the episode-corrected PAT label; do not compare the single-contact feature vector against PAT references
- Streaming baseline: use the first 75 ms of the 150 ms pre-roll, preventing a long first contact from contaminating the 200 ms offline baseline window and producing `no_touch_event`

## Verification

- Focused episode-rule regression: passed
- Full unit suite: 28/28 passed
- Gold full-fit replay: 315/315 model predictions correct; zero rules fired; no stored IMPACT was changed to PAT

The Gold replay is an in-sample safety check, not a new generalization metric. A live repeated-PAT action is required to verify the reported failure mode.
