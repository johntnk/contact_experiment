#!/usr/bin/env python3
"""Compute CoST-only capture compatibility metrics before freezing filter thresholds."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.cost import GESTURES, TARGET_MAPPING, VARIANTS, compatibility_metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "data/external/cost/v1/CoST.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/cost/cost_compatibility_metrics.csv")
    parser.add_argument("--summary", type=Path, default=ROOT / "artifacts/cost/cost_compatibility_summary.json")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.output.exists() or args.summary.exists():
        raise FileExistsError("refusing to overwrite compatibility artifacts")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    records, current_key, frames, capture_index = [], None, [], 0

    def finish():
        nonlocal frames, capture_index
        if not frames or (args.limit is not None and len(records) >= args.limit):
            return
        subject, variant, gesture = current_key
        source_gesture = GESTURES[gesture]
        mapped = TARGET_MAPPING.get(source_gesture)
        if mapped:
            capture_index += 1
            matrix = np.asarray(frames, dtype=float).reshape(-1, 8, 8)
            records.append({"source_capture_index": capture_index,
                            "source_subject": f"cost_subject_{subject:02d}",
                            "source_variant": VARIANTS[variant], "source_gesture": source_gesture,
                            "mapped_label": mapped, "frame_count": len(frames),
                            **compatibility_metrics(matrix)})
        frames = []

    with args.source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, skipinitialspace=True); next(reader)
        last_frame = 0
        for fields in reader:
            subject, variant, gesture, frame = map(int, fields[:4]); key = (subject, variant, gesture)
            if current_key is not None and (key != current_key or frame <= last_frame):
                finish()
                if args.limit is not None and len(records) >= args.limit:
                    break
            current_key, last_frame = key, frame
            frames.append(list(map(float, fields[4:])))
        else:
            finish()
    if not records:
        raise ValueError("no mapped captures found")
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)

    metric_names = ["pulse_count", "complete_release_count", "contact_area_ratio",
                    "trajectory_reversal_count", "trajectory_straightness", "active_fraction"]
    by_gesture = defaultdict(list)
    for row in records:
        by_gesture[row["source_gesture"]].append(row)
    summary = {"metric_version": "cost-compatibility-v1", "sampling_hz": 135.0,
               "rows": len(records), "class_counts": dict(Counter(row["mapped_label"] for row in records)),
               "source_gesture": {}}
    for gesture, rows in sorted(by_gesture.items()):
        summary["source_gesture"][gesture] = {"rows": len(rows)}
        for name in metric_names:
            values = np.asarray([float(row[name]) for row in rows])
            summary["source_gesture"][gesture][name] = {
                "min": float(values.min()), "p10": float(np.percentile(values, 10)),
                "p25": float(np.percentile(values, 25)), "median": float(np.median(values)),
                "p75": float(np.percentile(values, 75)), "p90": float(np.percentile(values, 90)),
                "max": float(values.max())}
    args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"rows": summary["rows"], "class_counts": summary["class_counts"],
                      "gestures": {key: {"rows": value["rows"],
                                          "pulse_median": value["pulse_count"]["median"],
                                          "area_median": value["contact_area_ratio"]["median"],
                                          "reversal_median": value["trajectory_reversal_count"]["median"],
                                          "straightness_median": value["trajectory_straightness"]["median"]}
                                   for key, value in summary["source_gesture"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
