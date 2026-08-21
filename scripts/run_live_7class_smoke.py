#!/usr/bin/env python3
"""Run one independent controlled live inference window for each class."""

from __future__ import annotations

import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["STATIC_TOUCH", "STROKE", "RUB", "TAP", "POKE", "PAT", "IMPACT"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to reuse live suite directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True)
    for index, label in enumerate(LABELS, 1):
        print(f"\n===== 七类现场验证 {index}/7：{label} =====", flush=True)
        output = args.output_dir / f"{index:02d}_{label.lower()}.json"
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/recognize_live.py"), "--expected-label", label,
             "--duration-s", "4", "--poll-interval-ms", "5", "--countdown-s", "3",
             "--output", str(output)],
            cwd=ROOT,
            check=True,
        )
    results = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.output_dir.glob("*.json"))]
    passed = sum(r["expected_match"] is True for r in results)
    print(f"\n七类现场 smoke 完成：Top-1 匹配 {passed}/7。")
    print("请勿据此单批结果调整模型；返回主会话进行统一审计。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
