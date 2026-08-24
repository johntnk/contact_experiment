"""CoST source-domain schema and capture indexing utilities."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


GESTURES = {
    1: "grab", 2: "hit", 3: "massage", 4: "pat", 5: "pinch", 6: "poke", 7: "press",
    8: "rub", 9: "scratch", 10: "slap", 11: "squeeze", 12: "stroke", 13: "tap", 14: "tickle",
}
TARGET_MAPPING = {
    "hit": "IMPACT", "pat": "PAT", "poke": "POKE", "press": "STATIC_TOUCH",
    "rub": "RUB", "slap": "IMPACT", "stroke": "STROKE", "tap": "TAP",
}
VARIANTS = {1: "gentle", 2: "normal", 3: "rough"}
MAPPING_VERSION = "cost-to-deepskin-v1"


def compatibility_metrics(matrix: np.ndarray, sampling_hz: float = 135.0) -> dict[str, float | int]:
    """Compute capture-level, sensor-normalized metrics used by the frozen CoST filter."""
    raw = np.asarray(matrix, dtype=np.float64)
    if raw.ndim != 3 or raw.shape[0] < 3:
        raise ValueError("compatibility metrics require a [T,H,W] capture with at least three frames")
    baseline_count = max(1, min(raw.shape[0] // 10, int(round(0.2 * sampling_hz))))
    corrected = np.maximum(raw - np.median(raw[:baseline_count], axis=0), 0.0)
    pressure = corrected.sum(axis=(1, 2))
    scale = float(np.percentile(pressure[pressure > 0], 95)) if np.any(pressure > 0) else 1.0
    normalized = pressure / max(scale, 1e-9)
    window = max(1, int(round(0.037 * sampling_hz)))
    smooth = np.convolve(normalized, np.ones(window) / window, mode="same")
    active = smooth >= 0.15
    min_run = max(1, int(round(0.022 * sampling_hz)))
    bridge = max(1, int(round(0.037 * sampling_hz)))

    def runs(mask):
        changes = np.diff(np.r_[False, mask, False].astype(np.int8))
        return list(zip(np.flatnonzero(changes == 1), np.flatnonzero(changes == -1)))

    for start, end in runs(active):
        if end - start < min_run:
            active[start:end] = False
    inactive = ~active
    for start, end in runs(inactive):
        if start > 0 and end < len(active) and end - start <= bridge:
            active[start:end] = True
    active_runs = runs(active)
    release_runs = [(start, end) for start, end in runs(~active)
                    if start > 0 and end < len(active) and end - start > bridge]

    positive = corrected[corrected > 0]
    taxel_scale = float(np.percentile(positive, 95)) if positive.size else 1.0
    area = (corrected > max(1e-9, 0.05 * taxel_scale)).mean(axis=(1, 2))
    contact_area = float(area[active].mean()) if np.any(active) else 0.0

    rows, cols = raw.shape[1:]
    yy, xx = np.mgrid[0:rows, 0:cols]
    denom = corrected.sum(axis=(1, 2)) + 1e-12
    cx = (corrected * xx).sum(axis=(1, 2)) / denom / max(cols - 1, 1)
    cy = (corrected * yy).sum(axis=(1, 2)) / denom / max(rows - 1, 1)
    points = np.column_stack([cx[active], cy[active]])
    if len(points) >= 2:
        smoothed = np.column_stack([np.convolve(points[:, axis], np.ones(window) / window, mode="same")
                                    for axis in range(2)]) if len(points) >= window else points
        delta = np.diff(smoothed, axis=0)
        steps = np.linalg.norm(delta, axis=1)
        path = float(steps.sum())
        displacement = float(np.linalg.norm(smoothed[-1] - smoothed[0]))
        major_axis = int(np.argmax(np.ptp(smoothed, axis=0)))
        component = delta[:, major_axis]
        movement_floor = max(0.002, float(np.percentile(np.abs(component), 50)))
        signs = np.sign(component[np.abs(component) >= movement_floor])
        reversals = int(np.sum(signs[1:] != signs[:-1])) if len(signs) > 1 else 0
        straightness = displacement / max(path, 1e-9)
    else:
        reversals, straightness = 0, 0.0
    return {"pulse_count": len(active_runs), "complete_release_count": len(release_runs),
            "contact_area_ratio": contact_area, "trajectory_reversal_count": reversals,
            "trajectory_straightness": float(straightness),
            "active_fraction": float(active.mean())}


def compatibility_filter_decision(source_gesture: str, metrics: dict, config: dict) -> tuple[str, str]:
    """Apply a frozen, source-only compatibility config to one mapped CoST capture."""
    rule = config["rules"].get(source_gesture)
    if rule is None:
        return "KEPT", "explicit_mapping_no_additional_filter"
    failures = []
    for name, expected in rule.items():
        value = float(metrics[name])
        if name.endswith("_eq"):
            continue
        if isinstance(expected, dict):
            if "eq" in expected and value != float(expected["eq"]): failures.append(f"{name}_not_eq_{expected['eq']}")
            if "min" in expected and value < float(expected["min"]): failures.append(f"{name}_below_{expected['min']}")
            if "max" in expected and value > float(expected["max"]): failures.append(f"{name}_above_{expected['max']}")
    return ("KEPT", "compatible") if not failures else ("FILTERED_AMBIGUOUS", ";".join(failures))


def audit_cost_csv(path: Path) -> tuple[dict, list[dict]]:
    captures: list[dict] = []
    subjects, gestures, variants = set(), set(), set()
    row_count = missing_values = bad_frame_steps = out_of_range = 0
    channel_min, channel_max = None, None
    current = None

    def finish_capture():
        if current is not None:
            captures.append(current.copy())

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, skipinitialspace=True)
        header = [item.strip() for item in next(reader)]
        expected = ["subject", "variant", "gesture", "frame"] + [f"ch{i}" for i in range(1, 65)]
        if header != expected:
            raise ValueError("CoST header does not match the documented 68-column schema")
        for source_row, fields in enumerate(reader, start=2):
            row_count += 1
            fields = [item.strip() for item in fields]
            if len(fields) != 68:
                raise ValueError(f"row {source_row} has {len(fields)} columns, expected 68")
            missing_values += sum(item == "" for item in fields)
            subject, variant, gesture, frame = map(int, fields[:4])
            channels = list(map(int, fields[4:]))
            subjects.add(subject); variants.add(variant); gestures.add(gesture)
            local_min, local_max = min(channels), max(channels)
            channel_min = local_min if channel_min is None else min(channel_min, local_min)
            channel_max = local_max if channel_max is None else max(channel_max, local_max)
            out_of_range += sum(value < 0 or value > 1023 for value in channels)
            key = (subject, variant, gesture)
            new_capture = current is None or key != current["_key"] or frame <= current["last_frame"]
            if new_capture:
                finish_capture()
                gesture_name = GESTURES.get(gesture)
                if gesture_name is None or variant not in VARIANTS:
                    raise ValueError(f"undocumented gesture/variant at row {source_row}")
                current = {
                    "_key": key,
                    "source_subject": f"cost_subject_{subject:02d}",
                    "source_variant": VARIANTS[variant],
                    "source_gesture_id": gesture,
                    "source_gesture": gesture_name,
                    "mapped_label": TARGET_MAPPING.get(gesture_name, ""),
                    "start_source_row": source_row,
                    "frame_count": 0,
                    "last_frame": 0,
                }
                if frame != 1:
                    bad_frame_steps += 1
            elif frame != current["last_frame"] + 1:
                bad_frame_steps += 1
            current["frame_count"] += 1
            current["last_frame"] = frame
    finish_capture()
    for index, capture in enumerate(captures, start=1):
        capture["source_capture_id"] = f"cost_capture_{index:06d}"
        capture["end_source_row"] = capture["start_source_row"] + capture["frame_count"] - 1
        capture.pop("_key"); capture.pop("last_frame")
    report = {
        "row_count": row_count,
        "column_count": 68,
        "channel_count": 64,
        "capture_count": len(captures),
        "subjects": sorted(subjects),
        "variants": sorted(variants),
        "gestures": sorted(gestures),
        "missing_values": missing_values,
        "bad_frame_steps": bad_frame_steps,
        "channel_min": channel_min,
        "channel_max": channel_max,
        "out_of_range_channel_values": out_of_range,
    }
    return report, captures
