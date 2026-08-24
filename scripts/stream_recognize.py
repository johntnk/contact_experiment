#!/usr/bin/env python3
"""Keep Deepskin enabled and emit accepted final gesture events continuously."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.rejection import apply_positive_gate
from deepskin_data.streaming import (ContactEventDetector, apply_episode_label_rule,
                                     count_micro_contacts, episode_gate_reference_label)
from deepskin_data.training import extract_features, segment_touch_event, transform_matrix
from deepskin_runtime import DeepskinSDK

DEFAULT_DLL = ROOT / "DeepskinSDK_Distribution_cpp_x64/bin/DeepskinSDK.dll"
DEFAULT_MODEL = ROOT / "models/deepskin_social_touch_v2"
ORIENTATIONS = {"normal": "original", "rotate_180": "both"}


def emit(payload: dict, output_format: str) -> None:
    if output_format == "label":
        print(payload["gesture"], flush=True)
    else:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), flush=True)


def classify_event(event, model, gate, schema, config, orientation_transform, threshold_scale=1.0):
    matrix = transform_matrix(event.matrix, orientation_transform)
    timestamps = event.timestamps_ms
    micro_contact_count = count_micro_contacts(matrix, timestamps)
    segment = {"found": True}
    if config.get("event_segmentation", False):
        matrix, timestamps, segment = segment_touch_event(
            matrix, timestamps, baseline_window_ms=75.0)
    feature, names = extract_features(matrix, timestamps)
    if names != schema:
        raise ValueError("stream feature schema disagrees with model package")
    model_prediction = str(model.predict(feature.reshape(1, -1))[0])
    prediction, classification_rule = apply_episode_label_rule(model_prediction, micro_contact_count)
    scores = model.decision_function(feature.reshape(1, -1))[0]
    ranked = sorted(((str(label), float(score)) for label, score in zip(model.classes_, scores)),
                    key=lambda item: item[1], reverse=True)
    scaled = model.named_steps["standardscaler"].transform(feature.reshape(1, -1))[0]
    gate_reference_label = episode_gate_reference_label(model_prediction, classification_rule)
    segment = dict(segment)
    segment.update({"micro_contact_count": micro_contact_count,
                    "model_prediction": model_prediction,
                    "classification_rule": classification_rule,
                    "gate_reference_label": gate_reference_label})
    gate_result = apply_positive_gate(
        scaled, gate_reference_label, gate, bool(segment.get("found")), threshold_scale=threshold_scale)
    gate_result["output_label"] = prediction if gate_result["accepted"] else "UNKNOWN"
    return prediction, ranked, gate_result, segment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dll", type=Path, default=DEFAULT_DLL)
    parser.add_argument("--model-package", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--orientation", choices=ORIENTATIONS, default="normal")
    parser.add_argument("--poll-interval-ms", type=float, default=5.0)
    parser.add_argument("--start-debounce-ms", type=float, default=40.0)
    parser.add_argument("--end-hold-ms", type=float, default=550.0,
                        help="Release hold used to aggregate nearby pulses (default: 550 ms)")
    parser.add_argument("--max-event-ms", type=float, default=8000.0)
    parser.add_argument("--output-format", choices=["jsonl", "label"], default="jsonl")
    parser.add_argument("--event-output", choices=["gesture-only", "all-events"], default="gesture-only")
    parser.add_argument("--gate-threshold-scale", type=float, default=1.2,
                        help="Positive-gate threshold multiplier; lower is stricter (default: 1.2)")
    parser.add_argument("--save-events-dir", type=Path)
    parser.add_argument("--max-runtime-s", type=float, help="Optional finite runtime for controlled validation")
    args = parser.parse_args()
    if args.output_format == "label" and args.event_output == "all-events":
        parser.error("label output only supports gesture-only events")
    if args.poll_interval_ms < 0 or args.max_event_ms <= 0:
        parser.error("poll interval must be non-negative and max event duration positive")
    if not np.isfinite(args.gate_threshold_scale) or args.gate_threshold_scale <= 0:
        parser.error("gate threshold scale must be a finite positive number")

    model = joblib.load(args.model_package / "model.joblib")
    gate_path = args.model_package / "positive_gate.joblib"
    if not gate_path.exists():
        raise FileNotFoundError("continuous target-only output requires positive_gate.joblib")
    gate = joblib.load(gate_path)
    schema = json.loads((args.model_package / "feature_schema.json").read_text(encoding="utf-8"))
    config = json.loads((args.model_package / "training_config.json").read_text(encoding="utf-8"))
    detector = ContactEventDetector(start_debounce_ms=args.start_debounce_ms,
                                    end_hold_ms=args.end_hold_ms, max_event_ms=args.max_event_ms)
    orientation_transform = ORIENTATIONS[args.orientation]
    sequence_no = 0
    started = time.monotonic()
    print("Deepskin continuous recognition started; press Ctrl+C to stop.", file=sys.stderr, flush=True)
    try:
        with DeepskinSDK(args.dll) as sdk:
            sdk.enable()
            rows, cols = sdk.matrix_size()
            if (rows, cols) != (18, 29):
                raise ValueError(f"model expects 18x29, device returned {rows}x{cols}")
            buffer = sdk.allocate_matrix(rows, cols)
            while args.max_runtime_s is None or time.monotonic() - started < args.max_runtime_s:
                sdk.read_matrix(buffer)
                timestamp_ms = (time.monotonic() - started) * 1000.0
                update = detector.update(np.asarray(buffer, dtype=float).reshape(rows, cols), timestamp_ms)
                if update.contact_started and args.event_output == "all-events":
                    sequence_no += 1
                    emit({"schema_version": "deepskin-stream-v1", "sequence_no": sequence_no,
                          "phase": "CONTACT_START", "recognition_state": "PENDING",
                          "timestamp_utc": datetime.now(timezone.utc).isoformat()}, args.output_format)
                if update.completed is not None:
                    event = update.completed
                    prediction, ranked, gate_result, segment = classify_event(
                        event, model, gate, schema, config, orientation_transform,
                        args.gate_threshold_scale)
                    event_id = f"evt_{event.event_index:06d}"
                    if args.save_events_dir is not None:
                        args.save_events_dir.mkdir(parents=True, exist_ok=True)
                        target = args.save_events_dir / f"{event_id}.npz"
                        if target.exists():
                            raise FileExistsError(f"refusing to overwrite saved event: {target}")
                        np.savez_compressed(target, matrix=event.matrix, timestamps_ms=event.timestamps_ms)
                    if gate_result["accepted"]:
                        sequence_no += 1
                        emit({"schema_version": "deepskin-stream-v1", "event_id": event_id,
                              "sequence_no": sequence_no, "phase": "GESTURE_END",
                              "recognition_state": "FINAL", "gesture": prediction, "final": True,
                              "duration_ms": float(event.timestamps_ms[-1]),
                              "forced_max_duration": event.forced_max_duration,
                              "gate_distance": gate_result["distance"],
                              "gate_threshold": gate_result["threshold"],
                              "ranked_decision_scores": [{"label": label, "score": score} for label, score in ranked],
                              "segment_info": segment,
                              "timestamp_utc": datetime.now(timezone.utc).isoformat()}, args.output_format)
                    else:
                        print(json.dumps({"event_id": event_id,
                                          "recognition_state": "SUPPRESSED_LOW_CONFIDENCE",
                                          "candidate": prediction, "reason": gate_result["reason"],
                                          "distance": gate_result["distance"],
                                          "threshold": gate_result["threshold"]}, ensure_ascii=False),
                              file=sys.stderr, flush=True)
                if args.poll_interval_ms:
                    time.sleep(args.poll_interval_ms / 1000.0)
    except KeyboardInterrupt:
        print("Deepskin continuous recognition stopped.", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
