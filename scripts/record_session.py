#!/usr/bin/env python3
"""Record or resume one complete 35-trial controlled Gold session."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from deepskin_data.recorder import collect_frames, finalize_metadata, validate_trial_directory, write_trial_atomic
from deepskin_data.recollection import load_recollection_plan
from deepskin_data.schema import GESTURE_LABELS, TRIAL_STATUSES, TrialMetadata
from deepskin_runtime.sdk import DeepskinSDK


DEFAULT_DLL = REPO_ROOT / "DeepskinSDK_Distribution_cpp_x64" / "bin" / "DeepskinSDK.dll"


class SimulatedSDK:
    """Deterministic acquisition stub used only by the session-runner smoke test."""

    def __init__(self) -> None:
        self.frame = 0

    def __enter__(self) -> "SimulatedSDK":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def enable(self) -> None:
        return None

    @staticmethod
    def matrix_size() -> tuple[int, int]:
        return 18, 29

    @staticmethod
    def allocate_matrix(rows: int, cols: int) -> list[float]:
        return [0.0] * (rows * cols)

    def read_matrix(self, buffer: list[float]) -> None:
        self.frame += 1
        for index in range(len(buffer)):
            buffer[index] = float((self.frame + index) % 7)

    def is_touching(self) -> bool:
        return self.frame % 3 == 0

    def current_json(self) -> str:
        return f'{{"simulated":true,"frame":{self.frame}}}'


def optional_text(value: str) -> str | None:
    return value or None


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
        if verified != instruction_label:
            print("验证标签与指令不一致；该执行不能标为 VALID，请选择 REDO 或 UNCERTAIN。")
            continue
        if input(f"输入 YES 确认 {instruction_label} -> {verified}: ").strip().upper() == "YES":
            return "VALID", verified, "CONTROLLED_CONFIRMED", "GOLD"
        print("未确认，请重新选择。")


def load_order(path: Path, operator_id: str, session_id: str) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 35:
        raise ValueError(f"session order must contain 35 rows, got {len(rows)}")
    for expected, row in enumerate(rows, start=1):
        if int(row["sequence"]) != expected:
            raise ValueError("session sequence is not contiguous")
        if row["operator_id"] != operator_id or row["session_id"] != session_id:
            raise ValueError("session order identity does not match CLI arguments")
        if row["instruction_label"] not in GESTURE_LABELS:
            raise ValueError(f"invalid order label: {row['instruction_label']}")
    return rows


def existing_attempts(session_root: Path, planned_trial_id: str) -> list[TrialMetadata]:
    paths = sorted(session_root.glob(f"{planned_trial_id}*/metadata.json"))
    attempts = [validate_trial_directory(path.parent) for path in paths]
    return [item for item in attempts if (item.planned_trial_id or item.trial_id) == planned_trial_id]


def completed_gold(attempts: list[TrialMetadata], minimum_attempt_no: int = 1) -> bool:
    return any(
        item.trial_status == "VALID"
        and item.attempt_no >= minimum_attempt_no
        and item.label_quality == "GOLD"
        and item.verified_label in GESTURE_LABELS
        and item.host_poll_rate_hz is not None
        for item in attempts
    )


def next_attempt(planned_trial_id: str, attempts: list[TrialMetadata]) -> tuple[str, int]:
    number = max((item.attempt_no for item in attempts), default=0) + 1
    trial_id = planned_trial_id if number == 1 else f"{planned_trial_id}_attempt_{number:02d}"
    return trial_id, number


def show_instruction(sequence: int, row: dict[str, str]) -> None:
    fields = [
        f"[{sequence:02d}/35] {row['instruction_label']}",
        f"intensity={row['intensity'] or '-'}",
        f"speed={row['speed'] or '-'}",
        f"direction={row['direction'] or '-'}",
        f"position={row['position'] or '-'}",
        f"contact_style={row['contact_style'] or '-'}",
        f"pulse_count={row['pulse_count'] or '-'}",
    ]
    print("\n" + " | ".join(fields))
    if row.get("notes"):
        print(f"说明：{row['notes']}")
    if row["instruction_label"] == "TAP":
        print("TAP 规则：快速接触一次（目标约 100–300 ms）后立即完全抬起；不要持续向下按压。")
    if row["instruction_label"] == "POKE":
        print("POKE 规则：指尖明确向下按入，短暂停留（目标约 500–1500 ms）后完全抬起；不要做成快速轻敲。")
    if row.get("pulse_count"):
        print(
            "PULSE 规则：每次短暂接触后必须完全抬起；下一次在相邻位置（约 1–2 cm）接触，"
            "不要原地连续压、不要滑动。"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--order", type=Path)
    parser.add_argument("--raw-root", type=Path, default=REPO_ROOT / "data" / "raw" / "deepskin")
    parser.add_argument("--dll", type=Path, default=DEFAULT_DLL)
    parser.add_argument("--duration-s", type=float, default=4.0)
    parser.add_argument("--poll-interval-ms", type=float, default=5.0)
    parser.add_argument("--countdown-s", type=int, default=3)
    parser.add_argument("--max-new-trials", type=int, help="safe partial-session/smoke limit")
    parser.add_argument("--simulate", action="store_true", help="use deterministic fake matrices")
    parser.add_argument(
        "--recollection-plan",
        type=Path,
        help="only record this operator/session's targets from a recollection plan",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    order_path = args.order or (
        REPO_ROOT / "protocol" / "session_orders" / f"{args.operator_id}_{args.session_id}.csv"
    )
    rows = load_order(order_path, args.operator_id, args.session_id)
    recollection = load_recollection_plan(args.recollection_plan)
    if args.recollection_plan:
        rows = [
            row
            for row in rows
            if (args.operator_id, args.session_id, row["trial_id"]) in recollection
        ]
        if not rows:
            raise ValueError("recollection plan has no targets for this operator/session")
    session_root = args.raw_root / args.operator_id / args.session_id
    new_trials = 0
    input(f"将录制/续采 {args.operator_id}/{args.session_id}。传感器空闲后按 Enter 初始化…")
    sdk_context = SimulatedSDK() if args.simulate else DeepskinSDK(args.dll)
    with sdk_context as sdk:
        sdk.enable()
        matrix_rows, matrix_cols = sdk.matrix_size()
        for row in rows:
            planned = row["trial_id"]
            attempts = existing_attempts(session_root, planned) if session_root.exists() else []
            minimum_attempt = recollection.get((args.operator_id, args.session_id, planned), 1)
            if completed_gold(attempts, minimum_attempt):
                print(f"跳过已完成 Gold：{planned}")
                continue
            if args.max_new_trials is not None and new_trials >= args.max_new_trials:
                print(f"已达到本次限制 {args.max_new_trials}，安全停止。")
                break
            trial_id, attempt_no = next_attempt(planned, attempts)
            show_instruction(int(row["sequence"]), row)
            input(f"准备 {trial_id}，完全松开后按 Enter…")
            for remaining in range(args.countdown_s, 0, -1):
                print(f"{remaining}…", flush=True)
                time.sleep(1)
            print(f"开始：请执行 {row['instruction_label']}", flush=True)
            arrays, events = collect_frames(sdk, args.duration_s, args.poll_interval_ms)
            print("结束：请停止动作并完全抬起。", flush=True)
            status, verified, label_source, label_quality = confirm_label(row["instruction_label"])
            pulse_count = int(row["pulse_count"]) if row["pulse_count"] else None
            metadata = TrialMetadata(
                operator_id=args.operator_id,
                session_id=args.session_id,
                trial_id=trial_id,
                planned_trial_id=planned,
                attempt_no=attempt_no,
                instruction_label=row["instruction_label"],
                verified_label=verified,
                trial_status=status,
                label_source=label_source,
                label_quality=label_quality,
                intensity_instruction=optional_text(row["intensity"]),
                speed_instruction=optional_text(row["speed"]),
                direction_instruction=optional_text(row["direction"]),
                position_instruction=optional_text(row["position"]),
                contact_style_instruction=optional_text(row["contact_style"]),
                pulse_count_instruction=pulse_count,
                device_model="eGalaxTouch_P81X32_A0KZ_v00_T0_k4.18.203",
                matrix_rows=matrix_rows,
                matrix_cols=matrix_cols,
                sampling_rate_observed_hz=1.0,
                recorded_at=datetime.now(timezone.utc).astimezone().isoformat(),
                frame_count=1,
                duration_ms=0.0,
                notes=row.get("notes", ""),
            )
            metadata = finalize_metadata(metadata, arrays)
            path = write_trial_atomic(args.raw_root, metadata, arrays, events)
            new_trials += 1
            print(f"已保存：{path.resolve()}")
    print(f"本次新录制 {new_trials} 个 trial。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
