#!/usr/bin/env python3
"""Stream CoST v1 captures into sensor-independent F0_common features."""

from __future__ import annotations

import argparse, csv, json, sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.cost import GESTURES, TARGET_MAPPING, VARIANTS
from deepskin_data.training import extract_common_features


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "data/external/cost/v1/CoST.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/features/cost_f0_common.csv")
    parser.add_argument("--coverage-report", type=Path, default=ROOT / "artifacts/features/cost_f0_coverage.json")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.output.exists() or args.coverage_report.exists():
        raise FileExistsError("refusing to overwrite CoST feature artifacts")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    capture_index, feature_rows, current_key, frames = 0, [], None, []
    names = None

    def finish():
        nonlocal capture_index, frames, names
        if not frames or (args.limit is not None and len(feature_rows) >= args.limit): return
        subject, variant, gesture = current_key
        source_label = GESTURES[gesture]
        target = TARGET_MAPPING.get(source_label)
        if target:
            capture_index += 1
            matrix = np.asarray([row[1] for row in frames], dtype=np.float64).reshape(-1, 8, 8)
            timestamps = np.arange(len(frames), dtype=np.float64) * (1000.0 / 135.0)
            feature, current_names = extract_common_features(matrix, timestamps)
            names = names or current_names
            if names != current_names: raise RuntimeError("feature schema changed between captures")
            feature_rows.append({"source_capture_index": capture_index, "source_subject": f"cost_subject_{subject:02d}",
                                 "source_variant": VARIANTS[variant], "source_gesture": source_label,
                                 "mapped_label": target, "frame_count": len(frames),
                                 **{name: value for name, value in zip(names, feature)}})
        frames = []

    with args.source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, skipinitialspace=True); next(reader)
        last_frame = 0
        for fields in reader:
            subject, variant, gesture, frame = map(int, fields[:4]); key = (subject, variant, gesture)
            if current_key is not None and (key != current_key or frame <= last_frame):
                finish()
                if args.limit is not None and len(feature_rows) >= args.limit: break
            current_key, last_frame = key, frame
            frames.append((frame, list(map(float, fields[4:]))))
        else: finish()
    if not feature_rows: raise ValueError("no mapped CoST captures were extracted")
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(feature_rows[0])); writer.writeheader(); writer.writerows(feature_rows)
    matrix = np.asarray([[row[name] for name in names] for row in feature_rows], dtype=float)
    report = {"feature_schema_version": "f0-common-v1", "rows": len(feature_rows), "feature_count": len(names),
              "finite": bool(np.isfinite(matrix).all()), "subjects": len({row["source_subject"] for row in feature_rows}),
              "class_counts": dict(sorted(Counter(row["mapped_label"] for row in feature_rows).items())),
              "feature_names": names}
    args.coverage_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "feature_names"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
