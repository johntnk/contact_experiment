#!/usr/bin/env python3
"""E1: train only on CoST F0_common and diagnose transfer to Deepskin Gold."""

from __future__ import annotations

import argparse, csv, json, sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.training import extract_common_features, load_manifest, load_trial, segment_touch_event

LABELS = ["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"]
META = {"source_capture_index", "source_subject", "source_variant", "source_gesture", "mapped_label", "frame_count"}


def model():
    return make_pipeline(StandardScaler(), SVC(C=10.0, gamma="scale", kernel="rbf", class_weight="balanced"))


def metrics(y_true, y_pred):
    return {"rows": len(y_true), "macro_f1": f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0),
            "balanced_accuracy": balanced_accuracy_score(y_true, y_pred), "accuracy": accuracy_score(y_true, y_pred),
            "confusion_matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cost-features", type=Path, default=ROOT / "artifacts/features/cost_f0_common_filtered.csv")
    parser.add_argument("--filter-report", type=Path, default=ROOT / "artifacts/cost/cost_filter_report.json")
    parser.add_argument("--gold-manifest", type=Path, default=ROOT / "data/processed/manifests/gold_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/evaluation/cost_source_only_v2")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.output_dir.exists(): raise FileExistsError(f"refusing to overwrite: {args.output_dir}")
    with args.cost_features.open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    if args.smoke:
        smoke_subjects = sorted({row["source_subject"] for row in source_rows})[:5]
        source_rows = [row for row in source_rows if row["source_subject"] in smoke_subjects]
    feature_names = [name for name in source_rows[0] if name not in META]
    xs = np.asarray([[float(row[name]) for name in feature_names] for row in source_rows])
    ys = np.asarray([row["mapped_label"] for row in source_rows])
    groups = np.asarray([row["source_subject"] for row in source_rows])
    source_pred = cross_val_predict(model(), xs, ys, groups=groups, cv=GroupKFold(5), method="predict")
    gold = load_manifest(args.gold_manifest)
    if args.smoke:
        seen, selected = {}, []
        for row in gold:
            key = (row["operator_id"], row["verified_label"])
            if seen.get(key, 0) < 2:
                selected.append(row); seen[key] = seen.get(key, 0) + 1
        gold = selected
    xt, yt, operators, ids = [], [], [], []
    for row in gold:
        matrix, timestamps = load_trial(args.raw_root, row)
        matrix, timestamps, _ = segment_touch_event(matrix, timestamps)
        feature, current_names = extract_common_features(matrix, timestamps)
        if current_names != feature_names: raise RuntimeError("CoST and Deepskin F0_common schemas differ")
        xt.append(feature); yt.append(row["verified_label"]); operators.append(row["operator_id"]); ids.append(row["planned_trial_id"])
    xt, yt, operators = np.vstack(xt), np.asarray(yt), np.asarray(operators)
    fitted = model().fit(xs, ys)
    target_pred = fitted.predict(xt)
    filter_report = json.loads(args.filter_report.read_text(encoding="utf-8"))
    result = {"experiment": "E1_cost_source_only_v2_filtered", "labels": LABELS,
              "source_training_rows": len(ys), "source_subjects": len(set(groups)), "target_test_rows": len(yt),
              "feature_schema_version": "f0-common-v1", "feature_count": len(feature_names),
              "model": {"family": "RBF-SVM", "C": 10.0, "gamma": "scale", "class_weight": "balanced"},
              "cost_filter_version": filter_report["filter_version"],
              "cost_filter_config_hash": filter_report["filter_config_sha256"],
              "cost_internal_group5fold": metrics(ys, source_pred), "deepskin_cross_domain": metrics(yt, target_pred),
              "deepskin_by_operator": {operator: metrics(yt[operators == operator], target_pred[operators == operator]) for operator in sorted(set(operators))},
              "limitation": "E1 is a domain-shift diagnostic and cannot be selected as the runtime model."}
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (args.output_dir / "deepskin_predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["operator_id", "planned_trial_id", "true_label", "predicted_label"])
        writer.writerows(zip(operators, ids, yt, target_pred))
    print(json.dumps({"cost_internal": result["cost_internal_group5fold"], "deepskin_cross_domain": result["deepskin_cross_domain"],
                      "deepskin_by_operator": result["deepskin_by_operator"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
