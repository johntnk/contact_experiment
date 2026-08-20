#!/usr/bin/env python3
"""Validate recorded trials and build the Gold-only CSV manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from deepskin_data.manifest import build_gold_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=REPO_ROOT / "data" / "raw" / "deepskin")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data" / "processed" / "manifests" / "gold_manifest.csv",
    )
    args = parser.parse_args()
    count = build_gold_manifest(args.raw_root, args.output)
    print(f"Wrote {count} validated Gold trials to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
