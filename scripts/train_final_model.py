#!/usr/bin/env python3
"""Train and package the selected final target-only Deepskin model."""

from __future__ import annotations

import argparse, csv, hashlib, json, shutil, sys
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
    parser.add_argument("--output", type=Path, default=ROOT / "models/deepskin_social_touch_v1")
    parser.add_argument("--model-version", default="1.0.0")
    parser.add_argument("--augmentation-policy", choices=sorted(AUGMENTATIONS), default="horizontal_vertical")
    parser.add_argument("--segment-events", action="store_true")
    parser.add_argument("--C", type=float, default=10.0)
    parser.add_argument("--gamma", default="0.01")
    parser.add_argument("--cv-macro-f1", type=float, default=0.8315819117395017)
    parser.add_argument("--cv-balanced-accuracy", type=float, default=0.8285714285714285)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite model package: {args.output}")
    rows = load_manifest(args.manifest)
    if len(rows) != 315 or sorted({r["verified_label"] for r in rows}) != LABELS:
        raise ValueError("expected the audited 315-row, seven-class Gold manifest")
    x, y, origins, feature_names = augmented_rows(
        rows, args.raw_root, args.augmentation_policy, segment_events=args.segment_events
    )
    expected_fit_rows = 315 * len(AUGMENTATIONS[args.augmentation_policy])
    if x.shape[0] != expected_fit_rows or len(set(o[:3] for o in origins)) != 315:
        raise ValueError("unexpected augmentation cardinality")
    gamma: str | float = args.gamma if args.gamma == "scale" else float(args.gamma)
    model = make_pipeline(
        StandardScaler(),
        SVC(C=args.C, gamma=gamma, kernel="rbf", class_weight="balanced"),
    ).fit(x, y)
    args.output.mkdir(parents=True)
    joblib.dump(model, args.output / "model.joblib")
    shutil.copyfile(args.manifest, args.output / "training_manifest.csv")
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
        "real_gold_trials": 315,
        "fitted_rows_after_augmentation": expected_fit_rows,
        "matrix_shape": [18, 29],
        "feature_count": len(feature_names),
        "selected_by": "nested Leave-One-Operator-Out modal configuration",
        "cross_validated_macro_f1": args.cv_macro_f1,
        "cross_validated_balanced_accuracy": args.cv_balanced_accuracy,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (args.output / "training_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (args.output / "label_map.json").write_text(json.dumps({str(i): v for i, v in enumerate(LABELS)}, indent=2), encoding="utf-8")
    (args.output / "feature_schema.json").write_text(json.dumps(feature_names, indent=2), encoding="utf-8")
    card = f"""# Deepskin social-touch model v{args.model_version}

Seven-class target-only RBF-SVM trained on all 315 audited real Gold trials. Policy: {args.augmentation_policy}; event segmentation: {args.segment_events}; fitted rows: {expected_fit_rows}. Fixed configuration: C={args.C}, gamma={gamma}, selected by nested Leave-One-Operator-Out validation.

Cross-validated performance on untouched original trials: Macro F1 {args.cv_macro_f1:.4f}, balanced accuracy {args.cv_balanced_accuracy:.4f}. These are cross-validation estimates, not training-set scores.

Classes: IMPACT, PAT, POKE, RUB, STATIC_TOUCH, STROKE, TAP.

Limitations: only three operators; all real data were collected with the left hand; results do not establish right-hand generalization. Input must use the exact 51-feature extractor, event-segmentation setting, and 18x29 matrix orientation recorded in this package.
"""
    (args.output / "model_card.md").write_text(card, encoding="utf-8")
    package_files = sorted(p for p in args.output.iterdir() if p.name != "checksums.sha256")
    (args.output / "checksums.sha256").write_text("".join(f"{sha256(p)}  {p.name}\n" for p in package_files), encoding="utf-8")
    print(json.dumps(config, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
