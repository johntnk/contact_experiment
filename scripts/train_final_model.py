#!/usr/bin/env python3
"""Train and package the selected final target-only Deepskin model."""

from __future__ import annotations

import argparse, csv, hashlib, json, shutil, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.training import AUGMENTATIONS, augmented_rows, load_manifest

LABELS = ["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/processed/manifests/gold_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    parser.add_argument("--output", type=Path, default=ROOT / "models/deepskin_social_touch_v3_target_only")
    parser.add_argument("--model-version", default="3.0.0")
    parser.add_argument("--augmentation-policy", choices=sorted(AUGMENTATIONS), default="none")
    parser.add_argument("--segment-events", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--C", type=float, default=10.0)
    parser.add_argument("--gamma", default="scale")
    parser.add_argument("--evaluation-metrics", type=Path,
                        default=ROOT / "artifacts/evaluation/cost_score_assisted_v2/metrics.json")
    parser.add_argument("--cost-provenance", type=Path, default=ROOT / "artifacts/cost/cost_provenance.json")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite model package: {args.output}")
    rows = load_manifest(args.manifest)
    if len(rows) != 315 or sorted({r["verified_label"] for r in rows}) != LABELS:
        raise ValueError("expected the audited 315-row, seven-class Gold manifest")
    if args.smoke:
        counts, selected = Counter(), []
        for row in rows:
            key = (row["operator_id"], row["verified_label"])
            if counts[key] < 2:
                selected.append(row); counts[key] += 1
        rows = selected
    x, y, origins, feature_names = augmented_rows(
        rows, args.raw_root, args.augmentation_policy, segment_events=args.segment_events
    )
    real_trials = 42 if args.smoke else 315
    expected_fit_rows = real_trials * len(AUGMENTATIONS[args.augmentation_policy])
    if x.shape[0] != expected_fit_rows or len(set(o[:3] for o in origins)) != real_trials:
        raise ValueError("unexpected augmentation cardinality")
    gamma: str | float = args.gamma if args.gamma == "scale" else float(args.gamma)
    scaler = StandardScaler().fit(x)
    classifier = SVC(C=args.C, gamma=gamma, kernel="rbf", class_weight="balanced").fit(scaler.transform(x), y)
    model = make_pipeline(scaler, classifier)
    args.output.mkdir(parents=True)
    joblib.dump(model, args.output / "model.joblib")
    joblib.dump(scaler, args.output / "preprocess.joblib")
    with (args.output / "training_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    evaluation = json.loads(args.evaluation_metrics.read_text(encoding="utf-8"))["baseline_pooled"]
    config = {
        "model_version": args.model_version,
        "training_recipe": "target_only",
        "model_family": "RBF-SVM",
        "C": args.C,
        "gamma": gamma,
        "class_weight": "balanced",
        "augmentation_policy": args.augmentation_policy,
        "augmentation_transforms": list(AUGMENTATIONS[args.augmentation_policy]),
        "event_segmentation": args.segment_events,
        "real_gold_trials": real_trials,
        "fitted_rows_after_augmentation": expected_fit_rows,
        "matrix_shape": [18, 29],
        "feature_count": len(feature_names),
        "selected_by": "nested Leave-One-Operator-Out modal configuration",
        "cross_validated_macro_f1": evaluation["macro_f1"],
        "cross_validated_balanced_accuracy": evaluation["balanced_accuracy"],
        "full_data_fit_is_not_a_new_test_score": True,
        "smoke": args.smoke,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (args.output / "training_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (args.output / "config.yaml").write_text(json.dumps(config, indent=2), encoding="utf-8")
    frozen_label_order = ["TAP", "POKE", "STATIC_TOUCH", "STROKE", "RUB", "PAT", "IMPACT"]
    (args.output / "label_map.json").write_text(json.dumps({str(i): v for i, v in enumerate(frozen_label_order)}, indent=2), encoding="utf-8")
    (args.output / "feature_schema.json").write_text(json.dumps(feature_names, indent=2), encoding="utf-8")
    (args.output / "metrics.json").write_text(json.dumps({
        "evaluation_protocol": "strict outer Leave-One-Operator-Out pooled predictions",
        "performance_claim_source": str(args.evaluation_metrics.relative_to(ROOT)),
        **evaluation,
    }, indent=2), encoding="utf-8")
    with (args.output / "confusion_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["true_label"] + LABELS)
        writer.writerows([[label] + values for label, values in zip(LABELS, evaluation["confusion_matrix"])])
    shutil.copyfile(args.cost_provenance, args.output / "cost_provenance.json")
    (args.output / "source_data_manifest.csv").write_text(
        "source_dataset,training_rows,note\nCoST,0,evaluated_but_not_used_in_target_only_training\n", encoding="utf-8")
    card = f"""# Deepskin social-touch model v{args.model_version}

Seven-class target-only RBF-SVM trained on {real_trials} audited real Gold trials. Policy: {args.augmentation_policy}; event segmentation: {args.segment_events}; fitted rows: {expected_fit_rows}. Fixed configuration: C={args.C}, gamma={gamma}, selected by nested Leave-One-Operator-Out validation.

Cross-validated performance on untouched original trials: Macro F1 {evaluation['macro_f1']:.4f}, balanced accuracy {evaluation['balanced_accuracy']:.4f}. These are outer cross-validation estimates, not a score from this full-data fit.

Classes: IMPACT, PAT, POKE, RUB, STATIC_TOUCH, STROKE, TAP.

CoST was evaluated but is not used for classifier training because no filtered transfer method passed the frozen gate. Training recipe: target_only.

Limitations: only three operators; all real data were collected with the left hand; results do not establish right-hand generalization. Input must use the exact 51-feature extractor, event-segmentation setting, and 18x29 matrix orientation recorded in this package.
"""
    (args.output / "model_card.md").write_text(card, encoding="utf-8")
    package_files = sorted(p for p in args.output.iterdir() if p.name != "checksums.sha256")
    checksum_text = "".join(f"{sha256(p)}  {p.name}\n" for p in package_files)
    (args.output / "checksums.sha256").write_text(checksum_text, encoding="utf-8")
    (args.output / "checksums.txt").write_text(checksum_text, encoding="utf-8")
    print(json.dumps(config, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
