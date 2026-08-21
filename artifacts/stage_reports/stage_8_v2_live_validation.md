# Stage 8 — model v2 seven-class live validation

Date: 2026-08-21

One protocol-controlled live window was captured for each of the seven classes using model v2. All seven Top-1 predictions matched the prompted class, compared with 3/7 in the earlier v1 live smoke.

Each result has a JSON record and same-stem raw NPZ. All raw hashes, model hashes, finite-value checks, and 18x29 shapes passed. Host poll rates ranged from 185.49 to 187.50 Hz. Segmented event durations were: STATIC_TOUCH 2719 ms, STROKE 718 ms, RUB 2407 ms, TAP 188 ms, POKE 1234 ms, PAT 359 ms, and IMPACT 391 ms. Every Top-1 decision score exceeded Top-2 by approximately 1.0 or more.

This passes the functional live-inference gate for SDK capture, event segmentation, feature extraction, model loading, and seven-class output. It is a smoke test with one trial per class and is not a new generalization estimate. Nested Leave-One-Operator-Out Macro F1 0.8535 remains the formal offline estimate.
