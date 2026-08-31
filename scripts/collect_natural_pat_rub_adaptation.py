#!/usr/bin/env python3
"""Collect an isolated natural-use PAT/RUB adaptation set."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAT_VARIANTS = [
    (2, "轻"), (3, "正常"), (4, "稍重"), (3, "轻"), (2, "正常"),
    (4, "正常"), (3, "稍重"), (2, "轻"), (4, "稍重"), (3, "正常"),
    (2, "稍重"), (4, "轻"), (3, "正常"), (2, "正常"), (4, "正常"),
]
RUB_VARIANTS = [
    (1, "慢"), (2, "正常"), (3, "快"), (2, "慢"), (1, "正常"),
    (3, "正常"), (2, "快"), (1, "慢"), (3, "快"), (2, "正常"),
    (1, "快"), (3, "慢"), (2, "正常"), (1, "正常"), (3, "正常"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to reuse adaptation directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True)

    schedule = []
    for index in range(15):
        schedule.append(("PAT", index + 1, PAT_VARIANTS[index]))
        schedule.append(("RUB", index + 1, RUB_VARIANTS[index]))

    for step, (label, repetition, variant) in enumerate(schedule, 1):
        if label == "PAT":
            count, intensity = variant
            instruction = (
                f"按自然习惯用较大接触面连续轻拍 {count} 次，力度：{intensity}。"
                "不必刻意悬空，但要有清楚的拍击节奏。"
            )
            variant_text = f"pulses{count}_{intensity}"
        else:
            cycles, speed = variant
            instruction = f"保持接触，自然往返摩擦 {cycles} 个来回，速度：{speed}；不要做成点按。"
            variant_text = f"cycles{cycles}_{speed}"
        print(f"\n===== 自然 PAT/RUB 适配采集 {step}/30：{label} 第 {repetition}/15 次 =====", flush=True)
        print(instruction, flush=True)
        print("请在采集开始后的前 3 秒完成动作，之后完全抬手并保持空闲到采集结束。", flush=True)
        output = args.output_dir / f"{step:02d}_{label.lower()}_{repetition:02d}_{variant_text}.json"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/recognize_live.py"),
                "--expected-label", label,
                "--duration-s", "5",
                "--poll-interval-ms", "5",
                "--countdown-s", "3",
                "--output", str(output),
            ],
            cwd=ROOT,
            check=True,
        )
    print("\n30 次适配训练数据采集完成。请返回主会话进行完整性审计。", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
