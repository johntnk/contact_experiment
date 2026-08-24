#!/usr/bin/env python3
"""E4: CoST-informed F0 feature subsets with Deepskin-only target training."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.training import extract_common_features, load_manifest, load_trial, segment_touch_event

LABELS = ["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"]
META = {"source_capture_index", "source_subject", "source_variant", "source_gesture",
        "mapped_label", "frame_count"}
SEEDS = [20260821, 20260822, 20260823]


def model(c=10.0, gamma="scale"):
    return make_pipeline(StandardScaler(), SVC(C=c, gamma=gamma, kernel="rbf", class_weight="balanced"))


def metrics(y_true, y_pred):
    return {"rows": int(len(y_true)),
            "macro_f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "per_class_f1": {label: float(value) for label, value in zip(
                LABELS, f1_score(y_true, y_pred, labels=LABELS, average=None, zero_division=0))},
            "confusion_matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist()}


def source_ranking(x, y, groups, names, seed, smoke):
    splits = min(5, len(set(groups)))
    fold_importances = []
    for fold_index, (train, test) in enumerate(GroupKFold(splits).split(x, y, groups)):
        fitted = model().fit(x[train], y[train])
        result = permutation_importance(fitted, x[test], y[test], scoring="f1_macro",
                                        n_repeats=1 if smoke else 3,
                                        random_state=seed + fold_index, n_jobs=-1)
        fold_importances.append(result.importances_mean)
    values = np.vstack(fold_importances)
    mean = values.mean(axis=0)
    order = sorted(range(len(names)), key=lambda index: (-mean[index], names[index]))
    top32 = set(order[:min(32, len(order))])
    records = [{"rank": rank + 1, "feature": names[index], "mean_importance": float(mean[index]),
                "std_across_folds": float(values[:, index].std()),
                "top32_fold_frequency": float(np.mean([
                    index in set(np.argsort(-fold_values)[:min(32, len(names))]) for fold_values in values]))}
               for rank, index in enumerate(order)]
    return order, records


def choose_target_config(x, y, operators, outer_train, subsets, grid):
    records = []
    for subset_size, indices in subsets.items():
        for c, gamma in grid:
            fold_scores = []
            for inner_operator in sorted(set(operators[outer_train])):
                inner_val = outer_train & (operators == inner_operator)
                inner_train = outer_train & (operators != inner_operator)
                fitted = model(c, gamma).fit(x[inner_train][:, indices], y[inner_train])
                fold_scores.append(f1_score(y[inner_val], fitted.predict(x[inner_val][:, indices]),
                                            labels=LABELS, average="macro", zero_division=0))
            records.append({"subset_size": int(subset_size), "C": c, "gamma": gamma,
                            "mean_macro_f1": float(np.mean(fold_scores)),
                            "fold_macro_f1": [float(value) for value in fold_scores]})
    selected = max(records, key=lambda row: (row["mean_macro_f1"], -row["subset_size"], -float(row["C"])))
    return selected, records


def paired_bootstrap(y, baseline, selected, seed, repetitions):
    rng = np.random.default_rng(seed)
    deltas = np.empty(repetitions)
    for index in range(repetitions):
        sample = rng.integers(0, len(y), len(y))
        base = f1_score(y[sample], baseline[sample], labels=LABELS, average="macro", zero_division=0)
        candidate = f1_score(y[sample], selected[sample], labels=LABELS, average="macro", zero_division=0)
        deltas[index] = candidate - base
    return {"repetitions": repetitions, "mean_delta": float(deltas.mean()),
            "ci95": [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))],
            "probability_positive": float(np.mean(deltas > 0))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cost-features", type=Path, default=ROOT / "artifacts/features/cost_f0_common_filtered.csv")
    parser.add_argument("--filter-report", type=Path, default=ROOT / "artifacts/cost/cost_filter_report.json")
    parser.add_argument("--gold-manifest", type=Path, default=ROOT / "data/processed/manifests/gold_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/evaluation/cost_feature_selected_v2")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output_dir}")

    with args.cost_features.open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    if args.smoke:
        subjects = sorted({row["source_subject"] for row in source_rows})[:5]
        source_rows = [row for row in source_rows if row["source_subject"] in subjects]
    feature_names = [name for name in source_rows[0] if name not in META]
    source_x = np.asarray([[float(row[name]) for name in feature_names] for row in source_rows])
    source_y = np.asarray([row["mapped_label"] for row in source_rows])
    source_groups = np.asarray([row["source_subject"] for row in source_rows])

    rows = load_manifest(args.gold_manifest)
    if args.smoke:
        counts, selected_rows = {}, []
        for row in rows:
            key = (row["operator_id"], row["verified_label"])
            if counts.get(key, 0) < 2:
                selected_rows.append(row); counts[key] = counts.get(key, 0) + 1
        rows = selected_rows
    target_x, target_y, operators, trial_ids = [], [], [], []
    for row in rows:
        matrix, timestamps = load_trial(args.raw_root, row)
        matrix, timestamps, _ = segment_touch_event(matrix, timestamps)
        features, current_names = extract_common_features(matrix, timestamps)
        if current_names != feature_names:
            raise RuntimeError("CoST and Deepskin F0_common schemas differ")
        target_x.append(features); target_y.append(row["verified_label"])
        operators.append(row["operator_id"]); trial_ids.append(row["planned_trial_id"])
    target_x, target_y, operators = np.vstack(target_x), np.asarray(target_y), np.asarray(operators)

    seeds = SEEDS[:1] if args.smoke else SEEDS
    subset_sizes = [16, len(feature_names)] if args.smoke else [16, 32, 48, len(feature_names)]
    grid = [(10.0, "scale")] if args.smoke else [(c, gamma) for c in (0.1, 1.0, 10.0, 100.0)
                                                    for gamma in ("scale", 0.01, 0.1, 1.0)]
    all_results, prediction_rows = [], []
    for seed in seeds:
        ranking, importance = source_ranking(source_x, source_y, source_groups, feature_names, seed, args.smoke)
        subsets = {size: np.asarray(ranking[:size], dtype=int) for size in subset_sizes}
        full = {len(feature_names): np.arange(len(feature_names), dtype=int)}
        baseline_oof = np.empty(len(target_y), dtype=object)
        selected_oof = np.empty(len(target_y), dtype=object)
        folds = []
        for outer_operator in sorted(set(operators)):
            outer_test = operators == outer_operator
            outer_train = ~outer_test
            baseline_config, baseline_search = choose_target_config(target_x, target_y, operators, outer_train, full, grid)
            selected_config, subset_search = choose_target_config(target_x, target_y, operators, outer_train, subsets, grid)
            base_indices = full[len(feature_names)]
            chosen_indices = subsets[selected_config["subset_size"]]
            baseline_model = model(baseline_config["C"], baseline_config["gamma"]).fit(
                target_x[outer_train][:, base_indices], target_y[outer_train])
            selected_model = model(selected_config["C"], selected_config["gamma"]).fit(
                target_x[outer_train][:, chosen_indices], target_y[outer_train])
            baseline_oof[outer_test] = baseline_model.predict(target_x[outer_test][:, base_indices])
            selected_oof[outer_test] = selected_model.predict(target_x[outer_test][:, chosen_indices])
            folds.append({"outer_test_operator": outer_operator,
                          "train_operators": sorted(set(operators[outer_train])),
                          "baseline_selected": baseline_config, "subset_selected": selected_config,
                          "selected_features": [feature_names[index] for index in chosen_indices],
                          "baseline_search": baseline_search, "subset_search": subset_search,
                          "baseline": metrics(target_y[outer_test], baseline_oof[outer_test]),
                          "selected": metrics(target_y[outer_test], selected_oof[outer_test])})
        entry = {"seed": seed, "source_importance": importance, "folds": folds,
                 "baseline_pooled": metrics(target_y, baseline_oof),
                 "selected_pooled": metrics(target_y, selected_oof),
                 "paired_bootstrap_macro_f1": paired_bootstrap(target_y, baseline_oof, selected_oof, seed,
                                                                200 if args.smoke else 2000)}
        all_results.append(entry)
        for operator, trial_id, truth, base, selected in zip(operators, trial_ids, target_y, baseline_oof, selected_oof):
            prediction_rows.append([seed, operator, trial_id, truth, base, selected])

    filter_report = json.loads(args.filter_report.read_text(encoding="utf-8"))
    result = {"experiment": "E4_cost_informed_feature_selection_v2_filtered", "smoke": args.smoke,
              "feature_schema_version": "f0-common-v1", "feature_count": len(feature_names),
              "candidate_subset_sizes": subset_sizes, "seeds": seeds,
              "source_rows": len(source_y), "source_subjects": len(set(source_groups)),
              "target_rows": len(target_y), "source_importance_method": "subject-grouped 5-fold permutation importance",
              "target_training_labels": "Deepskin outer-training operators only",
              "provenance": "artifacts/cost/cost_provenance.json",
              "cost_filter_version": filter_report["filter_version"],
              "cost_filter_config_hash": filter_report["filter_config_sha256"], "results": all_results}
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (args.output_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["seed", "operator_id", "planned_trial_id", "true_label",
                         "baseline_prediction", "selected_prediction"])
        writer.writerows(prediction_rows)
    print(json.dumps([{"seed": row["seed"], "baseline_macro_f1": row["baseline_pooled"]["macro_f1"],
                       "selected_macro_f1": row["selected_pooled"]["macro_f1"],
                       "delta": row["selected_pooled"]["macro_f1"] - row["baseline_pooled"]["macro_f1"],
                       "fold_deltas": [fold["selected"]["macro_f1"] - fold["baseline"]["macro_f1"] for fold in row["folds"]],
                       "selected_sizes": [fold["subset_selected"]["subset_size"] for fold in row["folds"]]}
                      for row in all_results], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
