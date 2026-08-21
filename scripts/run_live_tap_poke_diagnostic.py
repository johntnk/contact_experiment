#!/usr/bin/env python3
"""Collect three alternating raw-backed TAP/POKE live diagnostics per class."""

from __future__ import annotations

import argparse, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEQUENCE = ["TAP", "POKE", "TAP", "POKE", "TAP", "POKE"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to reuse diagnostic directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True)
    counts = {"TAP": 0, "POKE": 0}
    for index, label in enumerate(SEQUENCE, 1):
        counts[label] += 1
        print(f"\n===== TAP/POKE 诊断 {index}/6：{label} 第 {counts[label]} 次 =====", flush=True)
        output = args.output_dir / f"{index:02d}_{label.lower()}_{counts[label]:02d}.json"
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/recognize_live.py"), "--expected-label", label,
             "--duration-s", "4", "--poll-interval-ms", "5", "--countdown-s", "3", "--output", str(output)],
            cwd=ROOT, check=True,
        )
    print("\n六次原始波形诊断完成；请返回主会话统一审计。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
