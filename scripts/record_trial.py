#!/usr/bin/env python3
"""Record one controlled, explicitly confirmed Deepskin trial."""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from deepskin_data.recorder import collect_frames, finalize_metadata, write_trial_atomic
from deepskin_data.schema import GESTURE_LABELS, TRIAL_STATUSES, TrialMetadata
from deepskin_runtime.sdk import DeepskinSDK


DEFAULT_DLL = REPO_ROOT / "DeepskinSDK_Distribution_cpp_x64" / "bin" / "DeepskinSDK.dll"


def optional_text(value: str) -> str | None:
    return value or None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--instruction-label", choices=GESTURE_LABELS, required=True)
    parser.add_argument("--duration-s", type=float, default=5.0)
    parser.add_argument("--poll-interval-ms", type=float, default=5.0)
    parser.add_argument("--countdown-s", type=int, default=3)
    parser.add_argument("--intensity", default="")
    parser.add_argument("--speed", default="")
    parser.add_argument("--direction", default="")
    parser.add_argument("--position", default="")
    parser.add_argument("--contact-style", default="")
    parser.add_argument("--pulse-count", type=int)
    parser.add_argument("--notes", default="")
    parser.add_argument("--dll", type=Path, default=DEFAULT_DLL)
    parser.add_argument("--raw-root", type=Path, default=REPO_ROOT / "data" / "raw" / "deepskin")
    return parser.parse_args()


def confirm_label(instruction_label: str) -> tuple[str, str | None, str | None, str | None]:
    print("\n录制完成。必须人工确认，instruction_label 不会自动成为 Gold 标签。")
    while True:
        status = input("trial 状态 [VALID/REDO/UNCERTAIN]: ").strip().upper()
        if status not in TRIAL_STATUSES:
            print("无效状态，请重新输入。")
            continue
        if status != "VALID":
            return status, None, None, None
        verified = input(f"确认标签 {list(GESTURE_LABELS)}: ").strip().upper()
        if verified not in GESTURE_LABELS:
            print("无效标签，请重新输入状态和标签。")
            continue
        confirmation = input(f"输入 YES 确认 {instruction_label} -> {verified}: ").strip().upper()
        if confirmation == "YES":
            return "VALID", verified, "CONTROLLED_CONFIRMED", "GOLD"
        print("未确认，请重新选择。")


def main() -> int:
    args = parse_args()
    if args.duration_s <= 0 or args.poll_interval_ms < 0 or args.countdown_s < 0:
        raise SystemExit("duration, poll interval, or countdown is invalid")
    target = args.raw_root / args.operator_id / args.session_id / args.trial_id
    if target.exists():
        raise SystemExit(f"refusing to overwrite raw trial: {target}")
    input(f"准备录制 {args.instruction_label}。确认传感器空闲后按 Enter 开始…")
    for remaining in range(args.countdown_s, 0, -1):
        print(f"{remaining}…", flush=True)
        time.sleep(1)
    print(f"开始：请执行 {args.instruction_label}", flush=True)
    with DeepskinSDK(args.dll) as sdk:
        sdk.enable()
        rows, cols = sdk.matrix_size()
        arrays, events = collect_frames(sdk, args.duration_s, args.poll_interval_ms)
    print("结束：请停止动作并完全抬起。", flush=True)
    status, verified, label_source, label_quality = confirm_label(args.instruction_label)
    metadata = TrialMetadata(
        operator_id=args.operator_id,
        session_id=args.session_id,
        trial_id=args.trial_id,
        instruction_label=args.instruction_label,
        verified_label=verified,
        trial_status=status,
        label_source=label_source,
        label_quality=label_quality,
        intensity_instruction=optional_text(args.intensity),
        speed_instruction=optional_text(args.speed),
        direction_instruction=optional_text(args.direction),
        position_instruction=optional_text(args.position),
        contact_style_instruction=optional_text(args.contact_style),
        pulse_count_instruction=args.pulse_count,
        device_model="eGalaxTouch_P81X32_A0KZ_v00_T0_k4.18.203",
        matrix_rows=rows,
        matrix_cols=cols,
        sampling_rate_observed_hz=1.0,
        recorded_at=datetime.now(timezone.utc).astimezone().isoformat(),
        frame_count=1,
        duration_ms=0.0,
        notes=args.notes,
    )
    metadata = finalize_metadata(metadata, arrays)
    path = write_trial_atomic(args.raw_root, metadata, arrays, events)
    print(f"Saved immutable trial: {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
