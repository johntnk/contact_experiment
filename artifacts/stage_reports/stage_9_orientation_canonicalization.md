# Stage 9: Runtime orientation canonicalization

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `601fffee24debf3e0b3067036396c12d101ff9af`
- Model: `models/deepskin_social_touch_v2`
- GPU: not used
- Change: added deterministic `0°` / `180°` sensor-orientation selection to the desktop GUI and live CLI.
- Canonicalization: `0° -> original`; `180° -> reverse matrix rows and columns` (`both`).
- Ordering: canonicalization is applied before event segmentation and feature extraction.
- Provenance: raw NPZ matrices remain in device-native orientation; result JSON records the selected orientation and transform.
- Commands: `python -m py_compile scripts/social_touch_gui.py scripts/recognize_live.py`; `python -m unittest discover -s tests -v`; `python scripts/recognize_live.py --help`.
- Verification: syntax checks passed; all 16 unit tests passed; CLI exposes `--orientation {normal,rotate_180}`.
- Limitation: this stage validates transform correctness and software plumbing, not live accuracy after physical rotation. A paired hardware check in both orientations is the smallest next experiment.
