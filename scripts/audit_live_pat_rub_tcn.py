#!/usr/bin/env python3
"""Replay a controlled PAT/RUB diagnostic directory through the runtime TCN."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.cost import compatibility_metrics
from deepskin_data.streaming import ContactEventDetector, count_micro_contacts
from deepskin_temporal.model import SmallTCN
from deepskin_temporal.sequence import extract_event_sequence, extract_event_sequence_v2


def runtime_event(matrix: np.ndarray, timestamps_ms: np.ndarray):
    detector = ContactEventDetector(
        start_threshold=3.0,
        baseline_margin=2.0,
        start_debounce_ms=40.0,
        end_hold_ms=550.0,
        pre_roll_ms=150.0,
        max_event_ms=8000.0,
    )
    completed = None
    for frame, timestamp in zip(matrix, timestamps_ms):
        update = detector.update(frame, float(timestamp))
        if update.completed is not None:
            completed = update.completed
    if completed is None:
        raise ValueError("runtime detector did not complete an event")
    return completed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models/deepskin_temporal_tcn_v1")
    parser.add_argument("--expected-count", type=int, default=10)
    args = parser.parse_args()

    metadata_files = sorted(args.input_dir.glob("*.json"))
    if len(metadata_files) != args.expected_count:
        raise ValueError(f"expected {args.expected_count} diagnostic JSON files, found {len(metadata_files)}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.model_dir / "model.pt", map_location=device, weights_only=False)
    input_channels = int(checkpoint.get("input_channels", 21))
    feature_version = str(checkpoint.get("feature_version", "v1"))
    extractor = extract_event_sequence_v2 if feature_version == "v2" else extract_event_sequence
    model = SmallTCN(input_channels=input_channels).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    mean = np.asarray(checkpoint["channel_mean"], dtype=np.float32)
    std = np.asarray(checkpoint["channel_std"], dtype=np.float32)
    labels = list(checkpoint["labels"])

    results = []
    excluded = []
    for metadata_path in metadata_files:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        raw_path = metadata_path.with_suffix(".npz")
        with np.load(raw_path, allow_pickle=False) as archive:
            matrix = archive["matrix"]
            timestamps = archive["timestamps_ms"]
        if matrix.shape[1:] != (18, 29) or not np.isfinite(matrix).all():
            raise ValueError(f"invalid raw matrix: {raw_path}")
        try:
            event = runtime_event(matrix, timestamps)
        except ValueError as exc:
            excluded.append(
                {
                    "capture": metadata_path.stem,
                    "expected_label": str(metadata["expected_label"]),
                    "reason": str(exc),
                }
            )
            continue
        sequence, mask = extractor(event.matrix, event.timestamps_ms, baseline_window_ms=75.0)
        scaled = (((sequence - mean) / std) * mask[..., None]).astype(np.float32)
        with torch.inference_mode():
            logits = model(
                torch.from_numpy(scaled[None]).to(device),
                torch.from_numpy(mask[None]).to(device),
            )
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()
        order = np.argsort(probabilities)[::-1]
        ranked = [{"label": labels[index], "probability": float(probabilities[index])} for index in order]
        unique_t = np.unique(event.timestamps_ms)
        hz = 1000.0 / float(np.median(np.diff(unique_t)))
        metrics = compatibility_metrics(event.matrix, sampling_hz=hz)
        metrics["micro_contact_count"] = count_micro_contacts(event.matrix, event.timestamps_ms)
        expected = str(metadata["expected_label"])
        predicted = ranked[0]["label"]
        results.append(
            {
                "capture": metadata_path.stem,
                "expected_label": expected,
                "predicted_label": predicted,
                "correct": predicted == expected,
                "top3": ranked[:3],
                "metrics": metrics,
            }
        )

    confusion = Counter((row["expected_label"], row["predicted_label"]) for row in results)
    payload = {
        "schema_version": "pat-rub-live-tcn-audit-v1",
        "input_directory": str(args.input_dir.resolve()),
        "model_directory": str(args.model_dir.resolve()),
        "device": str(device),
        "feature_version": feature_version,
        "input_channels": input_channels,
        "requested_sample_count": len(metadata_files),
        "sample_count": len(results),
        "excluded_count": len(excluded),
        "excluded": excluded,
        "accuracy_diagnostic_only": sum(row["correct"] for row in results) / len(results),
        "confusion_counts": [
            {"expected_label": expected, "predicted_label": predicted, "count": count}
            for (expected, predicted), count in sorted(confusion.items())
        ],
        "results": results,
        "limitations": "Operator-specific, seen-session diagnostic only; not an independent test estimate.",
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite audit: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
