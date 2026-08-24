# Stage 11 / Plan Stage 4: CoST import and mapping

- Date: 2026-08-21
- Branch: `stage-3-gold-collection`
- Starting commit: `5b6356de871de1f0e36c3a52212f36818cdd2461`
- Source: Corpus of Social Touch (CoST), version 1, DOI `10.4121/uuid:5ef62345-3b3e-479c-8e1d-c922748c9b29`
- License: CC BY-NC-SA 4.0; attribution and raw-data policy recorded in `docs/cost_usage_record.md`.
- Official files: README 4,491 bytes and CoST.csv 455,810,440 bytes. Both official MD5 values matched; SHA-256 values are recorded in provenance.
- Raw-data policy: stored under ignored `data/external/cost/v1`; neither raw file is eligible for Git staging.
- Schema audit: 1,496,855 frames, 68 columns, 64 channels, 7,805 captures, 31 subjects, three variants, and 14 source gestures.
- Quality audit: zero missing values, zero frame-sequence violations, channel range 0–990, and zero values outside documented 0–1023.
- Mapping version: `cost-to-deepskin-v1`.
- Frozen mapping: tap→TAP, poke→POKE, press→STATIC_TOUCH, stroke→STROKE, rub→RUB, pat→PAT, hit/slap→IMPACT; all other source labels discarded.
- Retained source captures: 4,460. Counts: IMPACT 1,116; PAT 557; POKE 558; STATIC_TOUCH 558; RUB 557; STROKE 556; TAP 558.
- Verification: 18/18 unit tests passed; retained manifest has 31 subjects, no invalid row ranges, and all raw files are ignored by Git.
- Gate result: provenance, schema, explicit mapping, filtering, and source-subject traceability passed. No source-only or transfer-performance claim is made yet.

