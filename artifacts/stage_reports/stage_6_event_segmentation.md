# Stage 6 — event segmentation ablation

Date: 2026-08-21

Raw-backed TAP and POKE diagnostics motivated a baseline-relative event segmenter. It bridges gaps up to 100 ms, selects the longest active run, and retains 100 ms of context on both sides. The implementation was evaluated with the same nested Leave-One-Operator-Out protocol and untouched original outer-test trials.

| Configuration | Macro F1 | Balanced accuracy | Fold Macro F1 mean ± SD |
|---|---:|---:|---:|
| current: unsegmented + H/V/HV | 0.8316 | 0.8286 | 0.8326 ± 0.0404 |
| segmented + no flip | **0.8378** | **0.8381** | **0.8380 ± 0.0637** |
| segmented + H/V/HV | 0.8095 | 0.8095 | 0.8067 ± 0.0464 |

Segmented/no-flip improved POKE F1 from 0.6598 to 0.7253 and TAP F1 from 0.7347 to 0.7957. POKE-to-TAP errors fell from 10 to 6, while TAP-to-POKE remained 7. However, pooled Macro F1 improved by only 0.0062, below the 0.01 replacement gate, fold variance increased, and operator_03 Macro F1 dropped from 0.7800 to 0.7526. IMPACT and PAT also became worse.

Decision: retain the current packaged unsegmented H/V/HV model. Keep event segmentation as a diagnostic and possible class-specific component, but do not promote it to the final model without repeated raw-backed live evidence and a leakage-safe two-stage validation.
