#!/usr/bin/env python3
"""Audit the three frozen TCN outer folds against the matched V1 baseline."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"]


def labels_from_confusion(matrix):
    true, predicted = [], []
    for row_index, row in enumerate(matrix):
        for column_index, count in enumerate(row):
            true.extend([row_index] * int(count)); predicted.extend([column_index] * int(count))
    return np.asarray(true), np.asarray(predicted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--temporal-root", type=Path, default=ROOT / "artifacts/temporal")
    parser.add_argument("--v1-metrics", type=Path, default=ROOT / "artifacts/experiments/flip_ablation_corrected_segmented_full_v2/none/metrics.json")
    parser.add_argument("--v1-predictions", type=Path, default=ROOT / "artifacts/evaluation/cost_score_assisted_v2/predictions.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "models/deepskin_social_touch_v2/training_manifest.csv")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(f"refusing to overwrite audit: {args.output}")
    manifest = list(csv.DictReader(args.manifest.open(encoding="utf-8", newline="")))
    true, predicted, folds = [], [], []
    for operator_number in ("01", "02", "03"):
        directory = args.temporal_root / f"tcn_outer{operator_number}_v1"
        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        with (directory / "predictions.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 105: raise ValueError(f"incomplete predictions for operator_{operator_number}")
        true.extend(LABELS.index(row["true_label"]) for row in rows)
        predicted.extend(LABELS.index(row["predicted_label"]) for row in rows)
        operator = f"operator_{operator_number}"
        operator_manifest = [row for row in manifest if row["operator_id"] == operator]
        if len(operator_manifest) != len(rows): raise ValueError(f"manifest mismatch for {operator}")
        metric = report["metrics"]
        folds.append({"operator": report["outer_test_operator"], "selected_epochs": report["selected_epochs"],
                      "tcn_macro_f1": metric["macro_f1"],
                      "v1_macro_f1": metric["v1_same_fold_macro_f1_reference"],
                      "delta": metric["macro_f1"] - metric["v1_same_fold_macro_f1_reference"]})
    true = np.asarray(true); predicted = np.asarray(predicted)
    v1 = json.loads(args.v1_metrics.read_text(encoding="utf-8"))
    v1_true, v1_predicted = labels_from_confusion(v1["confusion_matrix"])
    tcn_per_class = f1_score(true, predicted, labels=range(7), average=None, zero_division=0)
    v1_per_class = f1_score(v1_true, v1_predicted, labels=range(7), average=None, zero_division=0)
    tcn_macro = float(f1_score(true, predicted, labels=range(7), average="macro", zero_division=0))
    with args.v1_predictions.open(encoding="utf-8", newline="") as handle:
        baseline_rows = list(csv.DictReader(handle))
    if len(baseline_rows) != len(manifest): raise ValueError("V1 prediction row count disagrees with manifest")
    for manifest_row, baseline_row in zip(manifest, baseline_rows):
        expected = (manifest_row["operator_id"], manifest_row["planned_trial_id"], manifest_row["verified_label"])
        observed = (baseline_row["operator_id"], baseline_row["planned_trial_id"], baseline_row["true_label"])
        if expected != observed: raise ValueError("V1 prediction order disagrees with manifest")
    baseline_prediction = np.asarray([LABELS.index(row["baseline_prediction"]) for row in baseline_rows])
    baseline_true = np.asarray([LABELS.index(row["true_label"]) for row in baseline_rows])
    if not np.array_equal(true, baseline_true): raise ValueError("V1 and TCN true-label order disagrees")
    baseline_macro = float(f1_score(true, baseline_prediction, labels=range(7), average="macro", zero_division=0))
    if not np.isclose(baseline_macro, v1["macro_f1"]): raise ValueError("row-level V1 metric does not match frozen metric")
    rng = np.random.default_rng(20260824); bootstrap = np.empty(10000, dtype=float)
    for index in range(len(bootstrap)):
        sample = rng.integers(0, len(true), len(true))
        bootstrap[index] = (f1_score(true[sample], predicted[sample], labels=range(7), average="macro", zero_division=0)
                            - f1_score(true[sample], baseline_prediction[sample], labels=range(7), average="macro", zero_division=0))
    per_class = {label: {"v1": float(old), "tcn": float(new), "delta": float(new - old)}
                 for label, old, new in zip(LABELS, v1_per_class, tcn_per_class)}
    gates = {"pooled_macro_f1_gain_at_least_0_01": tcn_macro - v1["macro_f1"] >= 0.01,
             "at_least_two_folds_non_decreasing": sum(fold["delta"] >= 0 for fold in folds) >= 2,
             "no_class_f1_drop_over_0_05": min(row["delta"] for row in per_class.values()) >= -0.05}
    result = {"schema_version": "deepskin-temporal-tcn-audit-v1", "rows": int(len(true)),
              "folds": folds, "tcn": {"macro_f1": tcn_macro,
              "balanced_accuracy": float(balanced_accuracy_score(true, predicted)),
              "accuracy": float(accuracy_score(true, predicted)),
              "confusion_matrix": confusion_matrix(true, predicted, labels=range(7)).tolist()},
              "v1": {key: v1[key] for key in ("macro_f1", "balanced_accuracy", "accuracy")},
              "macro_f1_delta": tcn_macro - v1["macro_f1"], "per_class_f1": per_class,
              "gates": gates, "selected_for_release": all(gates.values()),
              "paired_bootstrap": {"replicates": int(len(bootstrap)), "seed": 20260824,
                                   "mean_delta": float(bootstrap.mean()),
                                   "probability_positive": float((bootstrap > 0).mean()),
                                   "ci95": [float(np.percentile(bootstrap, 2.5)), float(np.percentile(bootstrap, 97.5))]}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
