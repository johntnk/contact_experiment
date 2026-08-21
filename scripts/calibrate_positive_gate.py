#!/usr/bin/env python3
"""Calibrate a conservative positive-only gate with leave-one-operator-out checks."""

from __future__ import annotations

import argparse, hashlib, json, sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.rejection import apply_positive_gate
from deepskin_data.training import augmented_rows, load_manifest

LABELS = ["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"]


def fit_classifier(x, y):
    return make_pipeline(StandardScaler(), SVC(C=10.0, gamma="scale", kernel="rbf", class_weight="balanced")).fit(x, y)


def cross_operator_distances(x, y, operators, scaler):
    z = scaler.transform(x)
    distances = {label: [] for label in LABELS}
    for index, (label, operator) in enumerate(zip(y, operators)):
        mask = (y == label) & (operators != operator)
        distances[label].append(float(np.linalg.norm(z[mask] - z[index], axis=1).min()))
    return distances


def make_gate(x, y, operators, scaler, quantile):
    z = scaler.transform(x)
    distances = cross_operator_distances(x, y, operators, scaler)
    return {
        "schema_version": "deepskin-positive-gate-v1",
        "method": "nearest same-class standardized feature; cross-operator quantile",
        "quantile": quantile,
        "thresholds": {label: float(np.quantile(distances[label], quantile)) for label in LABELS},
        "references": {label: z[y == label] for label in LABELS},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/processed/manifests/gold_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    parser.add_argument("--model-package", type=Path, default=ROOT / "models/deepskin_social_touch_v2")
    parser.add_argument("--quantile", type=float, default=0.90)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite gate report: {args.output}")
    if not 0.5 <= args.quantile < 1.0:
        raise ValueError("quantile must be in [0.5, 1.0)")
    rows = load_manifest(args.manifest)
    x, y, origins, names = augmented_rows(rows, args.raw_root, "none", segment_events=True)
    operators = np.asarray([origin[0] for origin in origins])
    fold_rows = []
    for held_out in sorted(set(operators)):
        train = operators != held_out
        test = ~train
        classifier = fit_classifier(x[train], y[train])
        scaler = classifier.named_steps["standardscaler"]
        train_ops = operators[train]
        gate = make_gate(x[train], y[train], train_ops, scaler, args.quantile)
        predicted = classifier.predict(x[test])
        scaled_test = scaler.transform(x[test])
        for truth, pred, feature in zip(y[test], predicted, scaled_test):
            decision = apply_positive_gate(feature, str(pred), gate)
            fold_rows.append({"operator": held_out, "truth": str(truth), "predicted": str(pred), **decision})
    accepted = [row for row in fold_rows if row["accepted"]]
    correct_accepted = [row for row in accepted if row["truth"] == row["predicted"]]
    correct_all = [row for row in fold_rows if row["truth"] == row["predicted"]]
    metrics = {
        "known_trials": len(fold_rows),
        "known_coverage": len(accepted) / len(fold_rows),
        "selective_precision": len(correct_accepted) / max(len(accepted), 1),
        "correct_target_yield": len(correct_accepted) / len(fold_rows),
        "baseline_accuracy": len(correct_all) / len(fold_rows),
        "accepted_incorrect": len(accepted) - len(correct_accepted),
        "rejected_known": len(fold_rows) - len(accepted),
    }
    final_model = joblib.load(args.model_package / "model.joblib")
    final_scaler = final_model.named_steps["standardscaler"]
    final_gate = make_gate(x, y, operators, final_scaler, args.quantile)
    joblib.dump(final_gate, args.model_package / "positive_gate.joblib")
    gate_path = args.model_package / "positive_gate.joblib"
    gate_sha256 = hashlib.sha256(gate_path.read_bytes()).hexdigest()
    (args.model_package / "positive_gate.sha256").write_text(
        f"{gate_sha256}  positive_gate.joblib\n", encoding="utf-8"
    )
    report = {
        "schema_version": "deepskin-positive-gate-calibration-v1",
        "quantile": args.quantile,
        "feature_count": len(names),
        "operators": sorted(set(operators)),
        "metrics": metrics,
        "final_thresholds": final_gate["thresholds"],
        "gate_sha256": gate_sha256,
        "limitation": "No unknown-class data were used; unknown rejection rate is not estimated.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
