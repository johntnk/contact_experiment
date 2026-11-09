#!/usr/bin/env python3
"""Measure the host-observed behavior of the public Deepskin SDK."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from deepskin_runtime import DeepskinSDK  # noqa: E402


DEFAULT_DLL = (
    REPO_ROOT
    / "DeepskinSDK_Distribution_cpp_x64"
    / "bin"
    / "DeepskinSDK.dll"
)
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "stage_reports" / "stage_1_probe.json"
CORNER_NAMES = ("TOP_LEFT", "TOP_RIGHT", "BOTTOM_RIGHT", "BOTTOM_LEFT")


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def describe(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "mean": statistics.fmean(values) if values else None,
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
    }


def matrix_signature(buffer: Iterable[float]) -> tuple[float, ...]:
    return tuple(buffer)


def weighted_centroid(values: list[float], tx: int, rx: int) -> tuple[float, float] | None:
    positive = [max(value, 0.0) for value in values]
    total = sum(positive)
    if total <= 0:
        return None
    x = sum((index % rx) * value for index, value in enumerate(positive)) / total
    y = sum((index // rx) * value for index, value in enumerate(positive)) / total
    return x / max(rx - 1, 1), y / max(tx - 1, 1)


def collect_probe(sdk: DeepskinSDK, duration_s: float, poll_interval_ms: float) -> dict[str, Any]:
    tx, rx = sdk.matrix_size()
    buffer = sdk.allocate_matrix(tx, rx)
    poll_intervals_ms: list[float] = []
    change_intervals_ms: list[float] = []
    sampled_values: list[float] = []
    previous_signature: tuple[float, ...] | None = None
    previous_poll_ns: int | None = None
    previous_change_ns: int | None = None
    polls = changed = touch_true = negative_values = total_values = 0
    json_result: dict[str, Any] = {"attempted": False, "ok": False}

    start_ns = time.monotonic_ns()
    deadline_ns = start_ns + int(duration_s * 1_000_000_000)
    while time.monotonic_ns() < deadline_ns:
        before_ns = time.monotonic_ns()
        sdk.read_matrix(buffer)
        now_ns = time.monotonic_ns()
        polls += 1
        if previous_poll_ns is not None:
            poll_intervals_ms.append((now_ns - previous_poll_ns) / 1_000_000)
        previous_poll_ns = now_ns

        values = list(buffer)
        signature = matrix_signature(values)
        if signature != previous_signature:
            changed += 1
            if previous_change_ns is not None:
                change_intervals_ms.append((now_ns - previous_change_ns) / 1_000_000)
            previous_change_ns = now_ns
            previous_signature = signature

        touch_true += int(sdk.is_touching())
        negative_values += sum(value < 0 for value in values)
        total_values += len(values)
        sampled_values.extend(values)

        if not json_result["attempted"]:
            json_result["attempted"] = True
            try:
                payload = sdk.current_json()
                json_result.update({"ok": True, "bytes": len(payload.encode("utf-8"))})
            except Exception as exc:  # JSON may be unavailable while idle.
                json_result.update({"error": str(exc)})

        elapsed_ms = (time.monotonic_ns() - before_ns) / 1_000_000
        sleep_ms = poll_interval_ms - elapsed_ms
        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000)

    end_ns = time.monotonic_ns()
    observed_s = (end_ns - start_ns) / 1_000_000_000
    return {
        "matrix": {"tx": tx, "rx": rx, "taxels": tx * rx, "layout": "row-major"},
        "timing": {
            "requested_duration_s": duration_s,
            "observed_duration_s": observed_s,
            "poll_interval_requested_ms": poll_interval_ms,
            "poll_count": polls,
            "host_poll_rate_hz": polls / observed_s if observed_s else None,
            "changed_matrix_count": changed,
            "host_observed_change_rate_hz": changed / observed_s if observed_s else None,
            "duplicate_matrix_count": polls - changed,
            "duplicate_matrix_ratio": (polls - changed) / polls if polls else None,
            "poll_intervals_ms": describe(poll_intervals_ms),
            "change_intervals_ms": describe(change_intervals_ms),
            "hardware_drop_count": None,
            "hardware_drop_count_reason": "public SDK exposes no hardware timestamp or sequence number",
        },
        "signal": {
            "values": describe(sampled_values),
            "negative_value_count": negative_values,
            "negative_value_ratio": negative_values / total_values if total_values else None,
            "touch_true_polls": touch_true,
            "touch_true_ratio": touch_true / polls if polls else None,
        },
        "current_json": json_result,
    }


def collect_orientation(sdk: DeepskinSDK, timeout_s: float) -> dict[str, Any]:
    tx, rx = sdk.matrix_size()
    buffer = sdk.allocate_matrix(tx, rx)
    results: dict[str, Any] = {}
    for corner in CORNER_NAMES:
        input(f"\n准备触摸 {corner}。先完全松开传感器，按 Enter 采集空闲基线…")
        baseline_frames: list[list[float]] = []
        for _ in range(30):
            sdk.read_matrix(buffer)
            baseline_frames.append(list(buffer))
            time.sleep(0.01)
        baseline = [
            statistics.median(frame[index] for frame in baseline_frames)
            for index in range(tx * rx)
        ]
        baseline_scores = [
            sum(abs(value - reference) for value, reference in zip(frame, baseline))
            for frame in baseline_frames
        ]
        detection_threshold = max(25.0, (percentile(baseline_scores, 0.99) or 0.0) * 5.0)
        print(f"现在触摸 {corner}，按住约 1 秒后完全抬起…")
        deadline = time.monotonic() + timeout_s
        best_score = 0.0
        best_delta: list[float] | None = None
        saw_signal = False
        while time.monotonic() < deadline:
            sdk.read_matrix(buffer)
            values = list(buffer)
            delta = [abs(value - reference) for value, reference in zip(values, baseline)]
            score = sum(delta)
            if score > best_score:
                best_score = score
                best_delta = delta
            if score >= detection_threshold:
                saw_signal = True
            elif saw_signal:
                break
            time.sleep(0.01)
        centroid = weighted_centroid(best_delta or [], tx, rx)
        if centroid is None or best_score < detection_threshold:
            raise RuntimeError(f"No usable touch was captured for {corner}")
        results[corner] = {
            "centroid_x_normalized": centroid[0],
            "centroid_y_normalized": centroid[1],
            "peak_absolute_delta": best_score,
            "detection_threshold": detection_threshold,
            "sdk_touch_flag_required": False,
        }
        print(f"捕获 {corner}: x={centroid[0]:.3f}, y={centroid[1]:.3f}")
    return results


def write_report(path: Path, report: dict[str, Any]) -> None:
    path = path.resolve()
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, default=DEFAULT_DLL)
    parser.add_argument("--duration-s", type=float, default=10.0)
    parser.add_argument("--poll-interval-ms", type=float, default=5.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--orientation", action="store_true")
    parser.add_argument("--corner-timeout-s", type=float, default=8.0)
    args = parser.parse_args()
    if args.duration_s <= 0:
        parser.error("--duration-s must be positive")
    if args.poll_interval_ms < 0:
        parser.error("--poll-interval-ms cannot be negative")
    return args


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "schema_version": "deepskin-stage1-probe-v1",
        "created_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "probe_scope": "host-observed public SDK behavior",
        "dll_path": str(args.dll.resolve()),
        "python_bits": 64 if sys.maxsize > 2**32 else 32,
    }
    try:
        with DeepskinSDK(args.dll) as sdk:
            sdk.enable()
            report["probe"] = collect_probe(sdk, args.duration_s, args.poll_interval_ms)
            if args.orientation:
                report["orientation"] = collect_orientation(sdk, args.corner_timeout_s)
    except Exception as exc:
        print(f"Probe failed: {exc}", file=sys.stderr)
        return 1

    try:
        write_report(args.output, report)
    except Exception as exc:
        print(f"Artifact write failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nSaved: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
