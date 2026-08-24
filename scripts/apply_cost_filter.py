#!/usr/bin/env python3
"""Apply the frozen CoST compatibility filter and build a filtered F0 feature table."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.cost import compatibility_filter_decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, default=ROOT / "artifacts/cost/cost_compatibility_metrics.csv")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts/features/cost_f0_common.csv")
    parser.add_argument("--config", type=Path, default=ROOT / "artifacts/cost/cost_filter_config.yaml")
    parser.add_argument("--decisions", type=Path, default=ROOT / "artifacts/cost/cost_filter_decisions.csv")
    parser.add_argument("--output-features", type=Path, default=ROOT / "artifacts/features/cost_f0_common_filtered.csv")
    parser.add_argument("--report", type=Path, default=ROOT / "artifacts/cost/cost_filter_report.json")
    parser.add_argument("--counts", type=Path, default=ROOT / "artifacts/cost/cost_filter_counts.csv")
    args = parser.parse_args()
    outputs = [args.decisions, args.output_features, args.report, args.counts]
    if any(path.exists() for path in outputs):
        raise FileExistsError("refusing to overwrite filtered CoST artifacts")
    config_bytes = args.config.read_bytes()
    config = json.loads(config_bytes.decode("utf-8"))
    with args.metrics.open(encoding="utf-8", newline="") as handle:
        metric_rows = list(csv.DictReader(handle))
    with args.features.open(encoding="utf-8", newline="") as handle:
        feature_rows = list(csv.DictReader(handle))
    by_index = {row["source_capture_index"]: row for row in feature_rows}
    if len(by_index) != len(feature_rows) or len(metric_rows) != len(feature_rows):
        raise RuntimeError("compatibility metrics and F0 features are not one-to-one")

    decisions, kept_features = [], []
    for row in metric_rows:
        feature = by_index.get(row["source_capture_index"])
        if feature is None or feature["source_gesture"] != row["source_gesture"]:
            raise RuntimeError("compatibility/feature capture identity mismatch")
        numeric = {key: float(value) for key, value in row.items()
                   if key in {"pulse_count", "complete_release_count", "contact_area_ratio",
                              "trajectory_reversal_count", "trajectory_straightness", "active_fraction"}}
        status, reason = compatibility_filter_decision(row["source_gesture"], numeric, config)
        decision = {**row, "filter_version": config["filter_version"],
                    "filter_status": status, "filter_reason": reason}
        decisions.append(decision)
        if status == "KEPT":
            kept_features.append(feature)
    if not kept_features:
        raise RuntimeError("filter retained no features")

    args.decisions.parent.mkdir(parents=True, exist_ok=True)
    with args.decisions.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decisions[0])); writer.writeheader(); writer.writerows(decisions)
    args.output_features.parent.mkdir(parents=True, exist_ok=True)
    with args.output_features.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(kept_features[0])); writer.writeheader(); writer.writerows(kept_features)

    before = Counter(row["mapped_label"] for row in decisions)
    after = Counter(row["mapped_label"] for row in decisions if row["filter_status"] == "KEPT")
    with args.counts.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["mapped_label", "before", "kept", "filtered"])
        for label in sorted(before): writer.writerow([label, before[label], after[label], before[label] - after[label]])
    report = {"filter_version": config["filter_version"],
              "filter_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
              "input_rows": len(decisions), "kept_rows": len(kept_features),
              "filtered_rows": len(decisions) - len(kept_features),
              "before": dict(sorted(before.items())), "after": dict(sorted(after.items())),
              "rules_frozen_without_deepskin_outcomes": True}
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
