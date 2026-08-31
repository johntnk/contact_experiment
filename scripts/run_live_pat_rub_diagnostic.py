#!/usr/bin/env python3
"""Collect five alternating raw-backed PAT/RUB live diagnostics per class."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEQUENCE = ["PAT", "RUB"] * 5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to reuse diagnostic directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True)

    counts = {"PAT": 0, "RUB": 0}
    for index, label in enumerate(SEQUENCE, 1):
        counts[label] += 1
        if label == "PAT":
            instruction = "用手掌或较大接触面在同一区域轻拍 2–4 次，每次都要完全卸力。"
        else:
            instruction = "保持接触，在皮肤上连续往返摩擦；中途不要主动抬手。"
        print(f"\n===== PAT/RUB 诊断 {index}/10：{label} 第 {counts[label]} 次 =====", flush=True)
        print(instruction, flush=True)
        output = args.output_dir / f"{index:02d}_{label.lower()}_{counts[label]:02d}.json"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/recognize_live.py"),
                "--expected-label",
                label,
                "--duration-s",
                "4",
                "--poll-interval-ms",
                "5",
                "--countdown-s",
                "3",
                "--output",
                str(output),
            ],
            cwd=ROOT,
            check=True,
        )
    print("\n10 次原始波形诊断已完成。请返回主会话进行 TCN 重放审计。", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
