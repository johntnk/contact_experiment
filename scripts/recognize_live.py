#!/usr/bin/env python3
"""Capture one controlled live window and classify it with the packaged model."""

from __future__ import annotations

import argparse, hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.recorder import collect_frames
from deepskin_data.rejection import apply_positive_gate
from deepskin_data.training import extract_features, segment_touch_event, transform_matrix
from deepskin_runtime import DeepskinSDK

DEFAULT_DLL = ROOT / "DeepskinSDK_Distribution_cpp_x64/bin/DeepskinSDK.dll"
DEFAULT_MODEL = ROOT / "models/deepskin_social_touch_v2"
ORIENTATION_TRANSFORMS = {"normal": "original", "rotate_180": "both"}
ACTION_INSTRUCTIONS = {
    "STROKE": "用一根手指从左向右单次划过，随后完全抬起；不要往返摩擦",
    "RUB": "保持接触并进行一次或多次往返摩擦",
    "STATIC_TOUCH": "轻触并保持位置不移动",
    "TAP": "快速轻敲后立即抬起",
    "POKE": "用指尖明确按戳一次后抬起",
    "PAT": "用较大接触面轻拍一次后抬起",
    "IMPACT": "用较大接触面快速、明显地冲击一次后抬起",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dll", type=Path, default=DEFAULT_DLL)
    p.add_argument("--model-package", type=Path, default=DEFAULT_MODEL)
    p.add_argument("--duration-s", type=float, default=4.0)
    p.add_argument("--poll-interval-ms", type=float, default=5.0)
    p.add_argument("--countdown-s", type=int, default=3)
    p.add_argument("--expected-label", choices=["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"])
    p.add_argument("--orientation", choices=ORIENTATION_TRANSFORMS, default="normal")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    raw_output = args.output.with_suffix(".npz")
    if args.output.exists() or raw_output.exists():
        raise FileExistsError(f"refusing to overwrite live result: {args.output} / {raw_output}")
    model_path = args.model_package / "model.joblib"
    model = joblib.load(model_path)
    gate_path = args.model_package / "positive_gate.joblib"
    gate = joblib.load(gate_path) if gate_path.exists() else None
    training_config = json.loads((args.model_package / "training_config.json").read_text(encoding="utf-8"))
    expected_features = json.loads((args.model_package / "feature_schema.json").read_text(encoding="utf-8"))
    action = args.expected_label or "任意一个七类动作"
    instruction = ACTION_INSTRUCTIONS.get(action, action)
    print(f"实时识别准备：{action} — {instruction}")
    input("传感器保持空闲；准备好后按 Enter 初始化设备…")
    with DeepskinSDK(args.dll) as sdk:
        sdk.enable()
        rows, cols = sdk.matrix_size()
        if (rows, cols) != (18, 29):
            raise ValueError(f"model expects 18x29, device returned {rows}x{cols}")
        print(f"设备已连接，{args.countdown_s} 秒后开始采集。")
        for remaining in range(args.countdown_s, 0, -1):
            print(f"倒计时 {remaining}…", flush=True); time.sleep(1)
        print(f"开始执行 {action}：{instruction}", flush=True)
        arrays, _ = collect_frames(sdk, args.duration_s, args.poll_interval_ms)
    orientation_transform = ORIENTATION_TRANSFORMS[args.orientation]
    feature_matrix = transform_matrix(arrays["matrix"], orientation_transform)
    feature_timestamps = arrays["timestamps_ms"]
    segment_info = {"found": False}
    if training_config.get("event_segmentation", False):
        feature_matrix, feature_timestamps, segment_info = segment_touch_event(feature_matrix, feature_timestamps)
    feature, names = extract_features(feature_matrix, feature_timestamps)
    if names != expected_features:
        raise ValueError("live feature schema disagrees with model package")
    prediction = str(model.predict(feature.reshape(1, -1))[0])
    gate_result = None
    output_label = prediction
    if gate is not None:
        scaled_feature = model.named_steps["standardscaler"].transform(feature.reshape(1, -1))[0]
        gate_result = apply_positive_gate(scaled_feature, prediction, gate, bool(segment_info.get("found")))
        output_label = gate_result["output_label"]
    scores = model.decision_function(feature.reshape(1, -1))[0]
    score_map = {str(label): float(score) for label, score in zip(model.classes_, scores)}
    ranked = sorted(score_map.items(), key=lambda item: item[1], reverse=True)
    matrix = arrays["matrix"]
    duration_ms = float(arrays["timestamps_ms"][-1])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(raw_output, **arrays)
    result = {
        "schema_version": "deepskin-live-inference-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_label": args.expected_label,
        "predicted_label": prediction,
        "output_label": output_label,
        "positive_gate": gate_result,
        "expected_match": None if args.expected_label is None else output_label == args.expected_label,
        "ranked_decision_scores": [{"label": k, "score": v} for k, v in ranked],
        "model_sha256": file_sha256(model_path),
        "raw_capture_file": raw_output.name,
        "raw_capture_sha256": file_sha256(raw_output),
        "event_segmentation": bool(training_config.get("event_segmentation", False)),
        "sensor_orientation": args.orientation,
        "orientation_transform": orientation_transform,
        "raw_matrix_orientation": "device_native",
        "segment_info": segment_info,
        "matrix_shape": list(matrix.shape),
        "frame_count": int(matrix.shape[0]),
        "duration_ms": duration_ms,
        "host_poll_rate_hz": float(matrix.shape[0] / max(duration_ms / 1000, 1e-9)),
        "matrix_min": float(matrix.min()),
        "matrix_max": float(matrix.max()),
        "matrix_finite": bool(np.isfinite(matrix).all()),
        "sdk_touch_true_frames": int(np.count_nonzero(arrays["touch_state"])),
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n识别结果：", output_label if output_label != "UNKNOWN" else "未识别（已忽略）")
    print("Top-3：", ", ".join(f"{k}={v:.3f}" for k, v in ranked[:3]))
    if args.expected_label:
        print("与指定动作一致：", "是" if result["expected_match"] else "否")
    print("结果已保存：", args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
