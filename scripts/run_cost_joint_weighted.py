#!/usr/bin/env python3
"""E2: leakage-safe, class/domain-balanced CoST + Deepskin joint training."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.training import (domain_class_sample_weights, extract_common_features,
                                    load_manifest, load_trial, segment_touch_event)

LABELS = ["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"]
META = {"source_capture_index", "source_subject", "source_variant", "source_gesture",
        "mapped_label", "frame_count"}
ALPHAS = [0.05, 0.10, 0.25, 0.50, 1.00]
SEEDS = [20260821, 20260822, 20260823]


def classifier(family: str, seed: int, smoke: bool = False):
    trees = 30 if smoke else 300
    if family == "rbf_svm":
        return make_pipeline(StandardScaler(), SVC(C=10.0, gamma="scale", kernel="rbf"))
    if family == "extra_trees":
        return ExtraTreesClassifier(n_estimators=trees, min_samples_leaf=2, n_jobs=-1, random_state=seed)
    if family == "random_forest":
        return RandomForestClassifier(n_estimators=trees, min_samples_leaf=2, n_jobs=-1,
                                      max_features="sqrt", random_state=seed)
    raise ValueError(f"unknown model family: {family}")


def fit_weighted(model, x, y, domains, alpha):
    weights = domain_class_sample_weights(y, domains, alpha)
    if hasattr(model, "named_steps"):
        model.fit(x, y, svc__sample_weight=weights)
    else:
        model.fit(x, y, sample_weight=weights)
    return model


def metric(y_true, y_pred):
    return {
        "rows": int(len(y_true)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "per_class_f1": {label: float(value) for label, value in zip(
            LABELS, f1_score(y_true, y_pred, labels=LABELS, average=None, zero_division=0))},
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist(),
    }


def paired_bootstrap(y, baseline, joint, seed, repetitions=2000):
    rng = np.random.default_rng(seed)
    deltas = np.empty(repetitions)
    for index in range(repetitions):
        sample = rng.integers(0, len(y), len(y))
        base_score = f1_score(y[sample], baseline[sample], labels=LABELS, average="macro", zero_division=0)
        joint_score = f1_score(y[sample], joint[sample], labels=LABELS, average="macro", zero_division=0)
        deltas[index] = joint_score - base_score
    return {"repetitions": repetitions, "mean_delta": float(deltas.mean()),
            "ci95": [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))],
            "probability_positive": float(np.mean(deltas > 0))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cost-features", type=Path, default=ROOT / "artifacts/features/cost_f0_common_filtered.csv")
    parser.add_argument("--filter-report", type=Path, default=ROOT / "artifacts/cost/cost_filter_report.json")
    parser.add_argument("--gold-manifest", type=Path, default=ROOT / "data/processed/manifests/gold_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/evaluation/cost_joint_weighted_v2")
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
    xs = np.asarray([[float(row[name]) for name in feature_names] for row in source_rows])
    ys = np.asarray([row["mapped_label"] for row in source_rows])

    target_rows = load_manifest(args.gold_manifest)
    if args.smoke:
        seen, selected = {}, []
        for row in target_rows:
            key = (row["operator_id"], row["verified_label"])
            if seen.get(key, 0) < 2:
                selected.append(row)
                seen[key] = seen.get(key, 0) + 1
        target_rows = selected
    xt, yt, operators, trial_ids = [], [], [], []
    for row in target_rows:
        matrix, timestamps = load_trial(args.raw_root, row)
        matrix, timestamps, _ = segment_touch_event(matrix, timestamps)
        features, current_names = extract_common_features(matrix, timestamps)
        if current_names != feature_names:
            raise RuntimeError("CoST and Deepskin F0_common schemas differ")
        xt.append(features); yt.append(row["verified_label"])
        operators.append(row["operator_id"]); trial_ids.append(row["planned_trial_id"])
    xt, yt, operators = np.vstack(xt), np.asarray(yt), np.asarray(operators)

    families = ["rbf_svm", "extra_trees", "random_forest"]
    seeds = SEEDS[:1] if args.smoke else SEEDS
    alphas = [0.05, 0.25] if args.smoke else ALPHAS
    results, prediction_rows = [], []
    for family in families:
        for seed in seeds:
            base_oof = np.empty(len(yt), dtype=object)
            joint_oof = np.empty(len(yt), dtype=object)
            folds = []
            for outer_operator in sorted(set(operators)):
                outer_test = operators == outer_operator
                outer_train = ~outer_test
                train_operators = sorted(set(operators[outer_train]))
                alpha_scores = {}
                for alpha in alphas:
                    scores = []
                    for inner_operator in train_operators:
                        inner_val = outer_train & (operators == inner_operator)
                        inner_train = outer_train & (operators != inner_operator)
                        x_train = np.vstack([xt[inner_train], xs])
                        y_train = np.concatenate([yt[inner_train], ys])
                        domains = np.concatenate([np.full(inner_train.sum(), "target"), np.full(len(ys), "source")])
                        fitted = fit_weighted(classifier(family, seed, args.smoke), x_train, y_train, domains, alpha)
                        scores.append(f1_score(yt[inner_val], fitted.predict(xt[inner_val]),
                                               labels=LABELS, average="macro", zero_division=0))
                    alpha_scores[str(alpha)] = float(np.mean(scores))
                selected_alpha = min(alphas, key=lambda value: (-alpha_scores[str(value)], value))

                target_domains = np.full(outer_train.sum(), "target")
                baseline = fit_weighted(classifier(family, seed, args.smoke), xt[outer_train], yt[outer_train],
                                        target_domains, 0.0)
                base_oof[outer_test] = baseline.predict(xt[outer_test])
                x_train = np.vstack([xt[outer_train], xs])
                y_train = np.concatenate([yt[outer_train], ys])
                domains = np.concatenate([target_domains, np.full(len(ys), "source")])
                joint = fit_weighted(classifier(family, seed, args.smoke), x_train, y_train, domains, selected_alpha)
                joint_oof[outer_test] = joint.predict(xt[outer_test])
                folds.append({"outer_test_operator": outer_operator, "train_operators": train_operators,
                              "selected_alpha": selected_alpha, "inner_alpha_macro_f1": alpha_scores,
                              "baseline": metric(yt[outer_test], base_oof[outer_test]),
                              "joint": metric(yt[outer_test], joint_oof[outer_test])})
            entry = {"family": family, "seed": seed, "folds": folds,
                     "baseline_pooled": metric(yt, base_oof), "joint_pooled": metric(yt, joint_oof),
                     "paired_bootstrap_macro_f1": paired_bootstrap(yt, base_oof, joint_oof, seed,
                                                                    200 if args.smoke else 2000)}
            results.append(entry)
            for operator, trial_id, truth, base_pred, joint_pred in zip(operators, trial_ids, yt, base_oof, joint_oof):
                prediction_rows.append([family, seed, operator, trial_id, truth, base_pred, joint_pred])

    filter_report = json.loads(args.filter_report.read_text(encoding="utf-8"))
    output = {"experiment": "E2_cost_joint_weighted_v2_filtered", "smoke": args.smoke,
              "feature_schema_version": "f0-common-v1", "feature_count": len(feature_names),
              "labels": LABELS, "alphas": alphas, "seeds": seeds,
              "source_rows": len(ys), "target_rows": len(yt),
              "weighting": "class-balanced within domain; target mean weight 1; source/target total ratio alpha",
              "provenance": "artifacts/cost/cost_provenance.json",
              "cost_filter_version": filter_report["filter_version"],
              "cost_filter_config_hash": filter_report["filter_config_sha256"], "results": results}
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "metrics.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    with (args.output_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["family", "seed", "operator_id", "planned_trial_id", "true_label",
                         "baseline_prediction", "joint_prediction"])
        writer.writerows(prediction_rows)
    print(json.dumps([{"family": row["family"], "seed": row["seed"],
                       "baseline_macro_f1": row["baseline_pooled"]["macro_f1"],
                       "joint_macro_f1": row["joint_pooled"]["macro_f1"],
                       "delta": row["joint_pooled"]["macro_f1"] - row["baseline_pooled"]["macro_f1"],
                       "selected_alphas": [fold["selected_alpha"] for fold in row["folds"]]}
                      for row in results], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
