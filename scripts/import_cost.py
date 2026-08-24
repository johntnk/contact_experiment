#!/usr/bin/env python3
"""Audit official CoST v1 and create versioned provenance/mapping artifacts."""

from __future__ import annotations

import argparse, csv, hashlib, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.cost import GESTURES, MAPPING_VERSION, TARGET_MAPPING, audit_cost_csv

OFFICIAL = {
    "dataset_url": "https://data.4tu.nl/datasets/bc4e5c6a-cfa4-4844-83e4-74a71cae3df6/1",
    "doi": "10.4121/uuid:5ef62345-3b3e-479c-8e1d-c922748c9b29",
    "license": "CC BY-NC-SA 4.0",
    "readme_md5": "454a2f2e38470fcb6087c891a85db238",
    "csv_md5": "c6035f76d1e13f81168dd79586dcb742",
}


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=ROOT / "data/external/cost/v1")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/cost")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite CoST artifacts: {args.output_dir}")
    readme, csv_path = args.source_dir / "README.txt", args.source_dir / "CoST.csv"
    hashes = {
        "README.txt": {"bytes": readme.stat().st_size, "md5": digest(readme, "md5"), "sha256": digest(readme, "sha256")},
        "CoST.csv": {"bytes": csv_path.stat().st_size, "md5": digest(csv_path, "md5"), "sha256": digest(csv_path, "sha256")},
    }
    if hashes["README.txt"]["md5"] != OFFICIAL["readme_md5"] or hashes["CoST.csv"]["md5"] != OFFICIAL["csv_md5"]:
        raise ValueError("downloaded CoST files do not match official MD5 values")
    schema, captures = audit_cost_csv(csv_path)
    kept = [row for row in captures if row["mapped_label"]]
    before = Counter(row["source_gesture"] for row in captures)
    after = Counter(row["mapped_label"] for row in kept)
    args.output_dir.mkdir(parents=True)
    provenance = {
        "schema_version": "deepskin-cost-provenance-v1",
        "dataset": "Corpus of Social Touch (CoST)",
        "version": 1,
        **OFFICIAL,
        "creator": "Merel Jung",
        "publisher": "4TU.ResearchData / University of Twente",
        "imported_at_utc": datetime.now(timezone.utc).isoformat(),
        "mapping_version": MAPPING_VERSION,
        "files": hashes,
    }
    (args.output_dir / "cost_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    (args.output_dir / "cost_schema_report.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    fields = ["source_capture_id", "source_subject", "source_variant", "source_gesture_id", "source_gesture", "mapped_label", "start_source_row", "end_source_row", "frame_count"]
    with (args.output_dir / "cost_source_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(kept)
    with (args.output_dir / "cost_class_counts_before_after.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["scope", "label", "capture_count"])
        for label in sorted(before): writer.writerow(["source", label, before[label]])
        for label in sorted(after): writer.writerow(["mapped", label, after[label]])
    mapping_lines = ["# CoST mapping report", "", f"Mapping version: `{MAPPING_VERSION}`", "", "| CoST label | Target label | Captures |", "|---|---:|---:|"]
    for gesture_id, label in GESTURES.items():
        mapping_lines.append(f"| {label} | {TARGET_MAPPING.get(label, 'discard')} | {before[label]} |")
    mapping_lines += ["", f"Kept captures: {len(kept)} / {len(captures)}.", "Ambiguous labels were not inferred; only the frozen explicit mapping was retained."]
    (args.output_dir / "cost_mapping_report.md").write_text("\n".join(mapping_lines) + "\n", encoding="utf-8")
    print(json.dumps({"schema": schema, "mapped_counts": after, "kept_captures": len(kept)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
