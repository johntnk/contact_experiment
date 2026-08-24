#!/usr/bin/env python3
"""E3: append seven CoST source-model scores to Deepskin target features."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.training import (extract_common_features, extract_features, load_manifest,
                                    load_trial, segment_touch_event)

LABELS = ["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"]
META = {"source_capture_index", "source_subject", "source_variant", "source_gesture",
        "mapped_label", "frame_count"}
SEEDS = [20260821, 20260822, 20260823]


def target_model(c, gamma):
    return make_pipeline(StandardScaler(), SVC(C=c, gamma=gamma, kernel="rbf", class_weight="balanced"))


def metrics(y_true, y_pred):
    return {"rows": int(len(y_true)),
            "macro_f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "per_class_f1": {label: float(value) for label, value in zip(
                LABELS, f1_score(y_true, y_pred, labels=LABELS, average=None, zero_division=0))},
            "confusion_matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist()}


def select_config(x, y, operators, outer_train, grid):
    scores = []
    for c, gamma in grid:
        fold_scores = []
        for inner_operator in sorted(set(operators[outer_train])):
            inner_val = outer_train & (operators == inner_operator)
            inner_train = outer_train & (operators != inner_operator)
            fitted = target_model(c, gamma).fit(x[inner_train], y[inner_train])
            fold_scores.append(f1_score(y[inner_val], fitted.predict(x[inner_val]),
                                        labels=LABELS, average="macro", zero_division=0))
        scores.append({"C": c, "gamma": gamma, "mean_macro_f1": float(np.mean(fold_scores)),
                       "fold_macro_f1": [float(value) for value in fold_scores]})
    best = max(scores, key=lambda row: (row["mean_macro_f1"], -float(row["C"]), -grid.index((row["C"], row["gamma"]))))
    return best, scores


def paired_bootstrap(y, baseline, assisted, seed, repetitions):
    rng = np.random.default_rng(seed)
    deltas = np.empty(repetitions)
    for index in range(repetitions):
        sample = rng.integers(0, len(y), len(y))
        a = f1_score(y[sample], baseline[sample], labels=LABELS, average="macro", zero_division=0)
        b = f1_score(y[sample], assisted[sample], labels=LABELS, average="macro", zero_division=0)
        deltas[index] = b - a
    return {"repetitions": repetitions, "mean_delta": float(deltas.mean()),
            "ci95": [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))],
            "probability_positive": float(np.mean(deltas > 0))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cost-features", type=Path, default=ROOT / "artifacts/features/cost_f0_common_filtered.csv")
    parser.add_argument("--filter-report", type=Path, default=ROOT / "artifacts/cost/cost_filter_report.json")
    parser.add_argument("--gold-manifest", type=Path, default=ROOT / "data/processed/manifests/gold_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/evaluation/cost_score_assisted_v2")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output_dir}")

    with args.cost_features.open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    if args.smoke:
        subjects = sorted({row["source_subject"] for row in source_rows})[:5]
        source_rows = [row for row in source_rows if row["source_subject"] in subjects]
    common_names = [name for name in source_rows[0] if name not in META]
    source_x = np.asarray([[float(row[name]) for name in common_names] for row in source_rows])
    source_y = np.asarray([row["mapped_label"] for row in source_rows])
    source_model = make_pipeline(StandardScaler(), SVC(C=10.0, gamma="scale", kernel="rbf",
                                                        class_weight="balanced"))
    source_model.fit(source_x, source_y)
    source_classes = list(source_model.classes_)
    if set(source_classes) != set(LABELS):
        raise RuntimeError(f"source model does not contain exactly seven labels: {source_classes}")

    rows = load_manifest(args.gold_manifest)
    if args.smoke:
        counts, selected = {}, []
        for row in rows:
            key = (row["operator_id"], row["verified_label"])
            if counts.get(key, 0) < 2:
                selected.append(row); counts[key] = counts.get(key, 0) + 1
        rows = selected
    f1_x, common_x, y, operators, trial_ids = [], [], [], [], []
    f1_names = None
    for row in rows:
        matrix, timestamps = load_trial(args.raw_root, row)
        matrix, timestamps, _ = segment_touch_event(matrix, timestamps)
        features, current_f1_names = extract_features(matrix, timestamps)
        common, current_common_names = extract_common_features(matrix, timestamps)
        if current_common_names != common_names:
            raise RuntimeError("CoST and Deepskin F0_common schemas differ")
        f1_names = f1_names or current_f1_names
        if current_f1_names != f1_names:
            raise RuntimeError("inconsistent Deepskin F1 schema")
        f1_x.append(features); common_x.append(common); y.append(row["verified_label"])
        operators.append(row["operator_id"]); trial_ids.append(row["planned_trial_id"])
    f1_x, common_x, y, operators = np.vstack(f1_x), np.vstack(common_x), np.asarray(y), np.asarray(operators)
    raw_scores = source_model.decision_function(common_x)
    score_order = [source_classes.index(label) for label in LABELS]
    source_scores = raw_scores[:, score_order]
    assisted_x = np.hstack([f1_x, source_scores])

    grid = [(10.0, "scale")] if args.smoke else [(c, gamma) for c in (0.1, 1.0, 10.0, 100.0)
                                                    for gamma in ("scale", 0.01, 0.1, 1.0)]
    base_oof = np.empty(len(y), dtype=object)
    assisted_oof = np.empty(len(y), dtype=object)
    folds = []
    for outer_operator in sorted(set(operators)):
        outer_test = operators == outer_operator
        outer_train = ~outer_test
        base_best, base_search = select_config(f1_x, y, operators, outer_train, grid)
        assisted_best, assisted_search = select_config(assisted_x, y, operators, outer_train, grid)
        base = target_model(base_best["C"], base_best["gamma"]).fit(f1_x[outer_train], y[outer_train])
        assisted = target_model(assisted_best["C"], assisted_best["gamma"]).fit(assisted_x[outer_train], y[outer_train])
        base_oof[outer_test] = base.predict(f1_x[outer_test])
        assisted_oof[outer_test] = assisted.predict(assisted_x[outer_test])
        folds.append({"outer_test_operator": outer_operator,
                      "train_operators": sorted(set(operators[outer_train])),
                      "baseline_selected": base_best, "assisted_selected": assisted_best,
                      "baseline_search": base_search, "assisted_search": assisted_search,
                      "baseline": metrics(y[outer_test], base_oof[outer_test]),
                      "assisted": metrics(y[outer_test], assisted_oof[outer_test])})

    bias = {}
    source_pred = np.asarray(LABELS)[np.argmax(source_scores, axis=1)]
    for label in LABELS:
        mask = y == label
        bias[label] = {"rows": int(mask.sum()),
                       "mean_decision_scores": {name: float(value) for name, value in zip(LABELS, source_scores[mask].mean(axis=0))},
                       "source_predicted_distribution": {name: int(np.sum(source_pred[mask] == name)) for name in LABELS}}
    seed_results = [{"seed": seed,
                     "paired_bootstrap_macro_f1": paired_bootstrap(y, base_oof, assisted_oof, seed,
                                                                    200 if args.smoke else 2000)}
                    for seed in (SEEDS[:1] if args.smoke else SEEDS)]
    filter_report = json.loads(args.filter_report.read_text(encoding="utf-8"))
    result = {"experiment": "E3_cost_score_assisted_v2_filtered", "smoke": args.smoke,
              "labels": LABELS, "source_training_rows": len(source_y), "target_rows": len(y),
              "source_model": {"family": "RBF-SVM", "C": 10.0, "gamma": "scale",
                               "training_labels": "CoST only", "score_order": LABELS},
              "target_model": {"family": "RBF-SVM", "nested_grid": grid,
                               "training_labels": "Deepskin outer-training operators only"},
              "feature_schema": {"baseline": "f1-deepskin-v1", "baseline_count": len(f1_names),
                                 "assisted": "f1-deepskin-v1+cost-scores-v1", "assisted_count": assisted_x.shape[1]},
              "folds": folds, "baseline_pooled": metrics(y, base_oof),
              "assisted_pooled": metrics(y, assisted_oof), "bootstrap_seeds": seed_results,
              "source_score_bias_on_deepskin": bias,
              "provenance": "artifacts/cost/cost_provenance.json",
              "cost_filter_version": filter_report["filter_version"],
              "cost_filter_config_hash": filter_report["filter_config_sha256"]}
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (args.output_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["operator_id", "planned_trial_id", "true_label", "baseline_prediction",
                         "assisted_prediction"] + [f"cost_score_{label}" for label in LABELS])
        for values in zip(operators, trial_ids, y, base_oof, assisted_oof, source_scores):
            writer.writerow(list(values[:5]) + list(values[5]))
    print(json.dumps({"baseline": result["baseline_pooled"], "assisted": result["assisted_pooled"],
                      "fold_deltas": [fold["assisted"]["macro_f1"] - fold["baseline"]["macro_f1"] for fold in folds],
                      "selected": [{"operator": fold["outer_test_operator"], "baseline": fold["baseline_selected"],
                                    "assisted": fold["assisted_selected"]} for fold in folds]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
