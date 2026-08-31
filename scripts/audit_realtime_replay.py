#!/usr/bin/env python3
"""Replay raw captures through the causal streaming window and stabilizer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.streaming import ContactEventDetector
from deepskin_temporal.model import SmallTCN
from deepskin_temporal.realtime import RealtimeLabelStabilizer
from deepskin_temporal.sequence import extract_realtime_window


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models/deepskin_temporal_tcn_adapted_v1")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--window-ms", type=int, default=1500)
    parser.add_argument("--interval-ms", type=int, default=100)
    parser.add_argument("--threshold", type=float, default=0.50)
    parser.add_argument("--initial-confirmations", type=int, default=3)
    parser.add_argument("--switch-confirmations", type=int, default=2)
    parser.add_argument("--end-hold-ms", type=int, default=550)
    parser.add_argument("--pat-initial-confirmations", type=int)
    parser.add_argument("--impact-initial-confirmations", type=int)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite replay audit: {args.output}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.model_dir / "model.pt", map_location=device, weights_only=False)
    model = SmallTCN(input_channels=int(checkpoint["input_channels"])).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    mean = np.asarray(checkpoint["channel_mean"], dtype=np.float32)
    std = np.asarray(checkpoint["channel_std"], dtype=np.float32)
    labels = list(checkpoint["labels"])

    results = []
    for metadata_path in sorted(args.input_dir.glob("*.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected = str(metadata["expected_label"])
        with np.load(metadata_path.with_suffix(".npz"), allow_pickle=False) as archive:
            matrix = archive["matrix"]
            timestamps = archive["timestamps_ms"]
        detector = ContactEventDetector(start_threshold=3.0, baseline_margin=2.0,
                                        start_debounce_ms=40.0, end_hold_ms=float(args.end_hold_ms),
                                        pre_roll_ms=150.0, max_event_ms=3_600_000.0)
        fast_confirmations = {}
        if args.pat_initial_confirmations is not None:
            fast_confirmations["PAT"] = args.pat_initial_confirmations
        if args.impact_initial_confirmations is not None:
            fast_confirmations["IMPACT"] = args.impact_initial_confirmations
        stabilizer = RealtimeLabelStabilizer(
            confidence_threshold=args.threshold,
            initial_confirmations=args.initial_confirmations,
            switch_confirmations=args.switch_confirmations,
            fast_initial_confirmations=fast_confirmations,
        )
        recent = []
        baseline = contact_start = None
        last_inference = float("-inf")
        outputs = []
        completed = False
        for frame, timestamp in zip(matrix, timestamps):
            timestamp = float(timestamp)
            recent.append((timestamp, frame.astype(float)))
            recent = [item for item in recent if timestamp - item[0] <= args.window_ms + 1000.0]
            threshold = detector.threshold
            active_now = float(np.maximum(frame, 0.0).max()) >= threshold
            update = detector.update(frame, timestamp)
            if update.contact_started:
                idle = [item for time_ms, item in recent if time_ms <= timestamp - 60.0]
                baseline = np.median(np.stack(idle[-60:] if idle else [recent[0][1]]), axis=0)
                contact_start = timestamp
                last_inference = float("-inf")
                stabilizer.reset()
            if detector.active and active_now and baseline is not None and contact_start is not None:
                if timestamp - contact_start >= 200.0 and timestamp - last_inference >= args.interval_ms:
                    selected = [(time_ms, item) for time_ms, item in recent
                                if time_ms >= timestamp - args.window_ms]
                    times = np.asarray([item[0] for item in selected])
                    frames = np.stack([item[1] for item in selected])
                    sequence, mask = extract_realtime_window(frames, times, baseline,
                                                             window_ms=args.window_ms)
                    scaled = (((sequence - mean) / std) * mask[..., None]).astype(np.float32)
                    with torch.inference_mode():
                        logits = model(torch.from_numpy(scaled[None]).to(device),
                                       torch.from_numpy(mask[None]).to(device))
                        probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()
                    top = int(np.argmax(probabilities))
                    stable = stabilizer.update(labels[top], float(probabilities[top]))
                    if stable.current_label is not None:
                        outputs.append({"elapsed_ms": timestamp - contact_start,
                                        "label": stable.current_label,
                                        "changed": stable.changed})
                    last_inference = timestamp
            if update.completed is not None:
                completed = True
                break
        first = outputs[0] if outputs else None
        first_correct = next((item for item in outputs if item["label"] == expected), None)
        results.append({
            "capture": metadata_path.stem,
            "expected_label": expected,
            "runtime_completed": completed,
            "output_count": len(outputs),
            "first_output": first,
            "first_correct_output": first_correct,
            "last_output_label": outputs[-1]["label"] if outputs else None,
            "distinct_output_labels": list(dict.fromkeys(item["label"] for item in outputs)),
        })
    complete = [item for item in results if item["runtime_completed"]]
    with_output = [item for item in complete if item["first_output"] is not None]
    correct_last = [item for item in with_output if item["last_output_label"] == item["expected_label"]]
    latencies = [item["first_correct_output"]["elapsed_ms"] for item in complete
                 if item["first_correct_output"] is not None]
    report = {
        "schema_version": "deepskin-realtime-replay-audit-v1",
        "config": {"window_ms": args.window_ms, "interval_ms": args.interval_ms,
                   "threshold": args.threshold, "initial_confirmations": args.initial_confirmations,
                   "switch_confirmations": args.switch_confirmations, "end_hold_ms": args.end_hold_ms,
                   "pat_initial_confirmations": args.pat_initial_confirmations,
                   "impact_initial_confirmations": args.impact_initial_confirmations},
        "captures": len(results),
        "runtime_complete": len(complete),
        "complete_with_output": len(with_output),
        "correct_last_output_development_only": len(correct_last),
        "median_first_correct_latency_ms": float(np.median(latencies)) if latencies else None,
        "results": results,
        "limitations": "Previously used adaptation data; pipeline/latency diagnostic only.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "results"},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
