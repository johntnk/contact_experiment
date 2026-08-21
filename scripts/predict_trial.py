#!/usr/bin/env python3
"""Run the packaged final model on one immutable recorded trial."""

from __future__ import annotations

import argparse, json, sys
from pathlib import Path
import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.training import extract_features, segment_touch_event

import numpy as np


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("trial", type=Path)
    p.add_argument("--model-package", type=Path, default=ROOT / "models/deepskin_social_touch_v1")
    args = p.parse_args()
    config = json.loads((args.model_package / "training_config.json").read_text(encoding="utf-8"))
    with np.load(args.trial / "matrix.npz", allow_pickle=False) as archive:
        matrix, timestamps = archive["matrix"], archive["timestamps_ms"]
    if config.get("event_segmentation", False):
        matrix, timestamps, _ = segment_touch_event(matrix, timestamps)
    feature, names = extract_features(matrix, timestamps)
    expected = json.loads((args.model_package / "feature_schema.json").read_text(encoding="utf-8"))
    if names != expected:
        raise ValueError("feature schema mismatch")
    prediction = joblib.load(args.model_package / "model.joblib").predict(feature.reshape(1, -1))[0]
    print(prediction)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
