# CoST transfer decision

> Superseded after the frozen compatibility filter was applied. The authoritative decision is `cost_transfer_decision_v2.md`; the final recipe is target-only.

Date: 2026-08-21

## Performance decision

E3 (`cost_score_assisted`) is the only surviving CoST-assisted performance candidate:

- Macro F1: 0.8535 target-only to 0.8656 assisted, delta +0.0121.
- Balanced accuracy: 0.8540 to 0.8667, delta +0.0127.
- Outer-fold Macro-F1 deltas: +0.0200, -0.0283, +0.0474; two of three folds improve.
- Worst class delta: PAT -0.0307, within the -0.05 limit.
- Minimum class F1 improves from 0.7312 to 0.7865.
- Operator-fold variance falls from 0.00286783 to 0.00081249.
- Paired bootstrap probability of positive gain is 0.801–0.819, although the 95% intervals include zero.

E1 is diagnostic only. E2 fails the two-non-decreasing-fold rule. E4 is negative across every seed.

## Release decision

E3 is **not yet approved for final training or runtime replacement**. The current CoST preparation performs explicit label mapping but does not implement the frozen capture-level compatibility filters for pulse count, complete releases, contact area, and trajectory reversal/straightness. Consequently:

- `artifacts/cost/cost_filter_config.yaml` is absent;
- no filter-config SHA-256 is recorded in E1–E4;
- the 4,460 source captures are mapped but not compatibility-filtered;
- model-package provenance gate 7 is incomplete.

The current Deepskin-only v2 model remains the runtime model and release fallback.

## Required next action

Implement and freeze CoST capture-level compatibility features and filtering using CoST-only statistics and the written action definitions, without inspecting outer-test outcomes. Generate the filter config and hash, rebuild source features, then rerun E1–E4. If E3 still passes all gates, freeze `training_recipe = cost_score_assisted` and build the complete model package; otherwise release the target-only fallback.
