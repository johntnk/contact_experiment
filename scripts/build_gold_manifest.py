#!/usr/bin/env python3
"""Validate recorded trials and build the Gold-only CSV manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECOLLECTION_PLAN = REPO_ROOT / "protocol" / "recollection_plans" / "gold_corrections_v2.csv"
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
    parser.add_argument(
        "--recollection-plan",
        type=Path,
        default=DEFAULT_RECOLLECTION_PLAN,
        help="minimum-attempt overrides for protocol-driven replacement trials",
    )
    args = parser.parse_args()
    count = build_gold_manifest(args.raw_root, args.output, args.recollection_plan)
    print(f"Wrote {count} validated Gold trials to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
