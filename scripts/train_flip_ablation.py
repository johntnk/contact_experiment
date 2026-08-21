#!/usr/bin/env python3
"""Compare no flip, horizontal flip, and horizontal+vertical flip with nested LOPO."""

from __future__ import annotations

import argparse, csv, json, sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.training import AUGMENTATIONS, augmented_rows, load_manifest

LABELS = ["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"]


def fit_model(x, y, c, gamma):
    return make_pipeline(StandardScaler(), SVC(C=c, gamma=gamma, kernel="rbf", class_weight="balanced")) .fit(x, y)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, default=ROOT / "data/processed/manifests/gold_manifest.csv")
    p.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--segment-events", action="store_true")
    args = p.parse_args()
    rows = load_manifest(args.manifest)
    if args.smoke:
        kept, counts = [], Counter()
        for row in rows:
            key = (row["operator_id"], row["verified_label"])
            if counts[key] < 2:
                kept.append(row); counts[key] += 1
        rows = kept
    operators = sorted({r["operator_id"] for r in rows})
    if len(operators) != 3:
        raise ValueError("exactly three operators are required")
    c_grid = [1.0] if args.smoke else [0.1, 1.0, 10.0, 100.0]
    gamma_grid = ["scale"] if args.smoke else ["scale", 0.01, 0.1, 1.0]
    args.output.mkdir(parents=True, exist_ok=False)
    feature_cache, trial_cache = {}, {}
    def dataset(selected_rows, policy):
        return augmented_rows(selected_rows, args.raw_root, policy, feature_cache, trial_cache, args.segment_events)
    all_results = {}
    for policy in AUGMENTATIONS:
        policy_dir = args.output / policy; policy_dir.mkdir()
        predictions, fold_results, feature_names = [], [], None
        for outer in operators:
            train_rows = [r for r in rows if r["operator_id"] != outer]
            test_rows = [r for r in rows if r["operator_id"] == outer]
            inner_ops = sorted({r["operator_id"] for r in train_rows})
            scored = []
            for c in c_grid:
                for gamma in gamma_grid:
                    scores = []
                    for val_op in inner_ops:
                        inner_train = [r for r in train_rows if r["operator_id"] != val_op]
                        inner_val = [r for r in train_rows if r["operator_id"] == val_op]
                        xtr, ytr, _, feature_names = dataset(inner_train, policy)
                        xv, yv, _, _ = dataset(inner_val, "none")
                        scores.append(f1_score(yv, fit_model(xtr, ytr, c, gamma).predict(xv), average="macro"))
                    scored.append((float(np.mean(scores)), c, gamma))
            _, best_c, best_gamma = max(scored, key=lambda z: (z[0], -float(z[1])))
            xtr, ytr, origins, feature_names = dataset(train_rows, policy)
            xt, yt, test_origins, _ = dataset(test_rows, "none")
            if any(origin[0] == outer for origin in origins):
                raise RuntimeError("operator leakage detected")
            model = fit_model(xtr, ytr, best_c, best_gamma)
            yp = model.predict(xt)
            joblib.dump(model, policy_dir / f"model_test_{outer}.joblib")
            fold = {"test_operator": outer, "best_C": best_c, "best_gamma": best_gamma,
                    "train_rows_real": len(train_rows), "train_rows_augmented": len(ytr), "test_rows": len(yt),
                    "macro_f1": f1_score(yt, yp, average="macro"),
                    "balanced_accuracy": balanced_accuracy_score(yt, yp), "accuracy": accuracy_score(yt, yp),
                    "confusion_matrix": confusion_matrix(yt, yp, labels=LABELS).tolist()}
            fold_results.append(fold)
            for origin, true, pred in zip(test_origins, yt, yp):
                predictions.append({"operator_id": origin[0], "session_id": origin[1], "planned_trial_id": origin[2], "true_label": true, "predicted_label": pred})
        true = np.asarray([p["true_label"] for p in predictions]); pred = np.asarray([p["predicted_label"] for p in predictions])
        summary = {"policy": policy, "event_segmentation": args.segment_events, "augmentation_multiplier": len(AUGMENTATIONS[policy]), "real_gold_rows": len(rows),
                   "evaluated_original_rows": len(predictions), "labels": LABELS, "folds": fold_results,
                   "macro_f1": f1_score(true, pred, average="macro"), "balanced_accuracy": balanced_accuracy_score(true, pred),
                   "accuracy": accuracy_score(true, pred), "confusion_matrix": confusion_matrix(true, pred, labels=LABELS).tolist()}
        (policy_dir / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (policy_dir / "feature_schema.json").write_text(json.dumps(feature_names, indent=2), encoding="utf-8")
        with (policy_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as h:
            w = csv.DictWriter(h, fieldnames=predictions[0]); w.writeheader(); w.writerows(predictions)
        all_results[policy] = summary
    comparison = {p: {k: v[k] for k in ("augmentation_multiplier", "macro_f1", "balanced_accuracy", "accuracy")} for p, v in all_results.items()}
    (args.output / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    print(json.dumps(comparison, indent=2)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
