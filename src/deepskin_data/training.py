"""Leakage-safe feature extraction and flip augmentation for Deepskin trials."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


AUGMENTATIONS = {
    "none": ("original",),
    "horizontal": ("original", "horizontal"),
    "horizontal_vertical": ("original", "horizontal", "vertical", "both"),
}


def transform_matrix(matrix: np.ndarray, transform: str) -> np.ndarray:
    if transform == "original":
        return matrix
    if transform == "horizontal":
        return matrix[:, :, ::-1]
    if transform == "vertical":
        return matrix[:, ::-1, :]
    if transform == "both":
        return matrix[:, ::-1, ::-1]
    raise ValueError(f"unknown transform: {transform}")


def extract_features(matrix: np.ndarray, timestamps_ms: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Extract fixed-length pressure, area, temporal, and trajectory features."""
    x = np.abs(np.asarray(matrix, dtype=np.float64))
    t, rows, cols = x.shape
    pressure = x.sum(axis=(1, 2))
    threshold = max(1.0, float(np.percentile(x, 75)))
    area = (x > threshold).sum(axis=(1, 2)).astype(float)
    yy, xx = np.mgrid[0:rows, 0:cols]
    denom = pressure + 1e-9
    cx = (x * xx).sum(axis=(1, 2)) / denom / max(cols - 1, 1)
    cy = (x * yy).sum(axis=(1, 2)) / denom / max(rows - 1, 1)
    dx, dy = np.diff(cx), np.diff(cy)
    movement = np.hypot(dx, dy)
    dp = np.diff(pressure)
    dt = np.diff(np.asarray(timestamps_ms, dtype=float)) / 1000.0
    duration = max(float(timestamps_ms[-1] - timestamps_ms[0]) / 1000.0, 1e-9)

    values: list[float] = []
    names: list[str] = []

    def add_stats(prefix: str, a: np.ndarray) -> None:
        a = np.asarray(a, dtype=float)
        for suffix, value in (
            ("mean", a.mean()), ("std", a.std()), ("min", a.min()),
            ("max", a.max()), ("p25", np.percentile(a, 25)),
            ("p50", np.percentile(a, 50)), ("p75", np.percentile(a, 75)),
        ):
            names.append(f"{prefix}_{suffix}")
            values.append(float(value))

    add_stats("pressure", pressure)
    add_stats("area", area)
    add_stats("centroid_x", cx)
    add_stats("centroid_y", cy)
    add_stats("movement", movement if movement.size else np.zeros(1))
    for name, value in (
        ("duration_s", duration), ("frame_count", t),
        ("pressure_integral", np.trapezoid(pressure, dx=duration / max(t - 1, 1))),
        ("pressure_abs_derivative_mean", np.abs(dp).mean()),
        ("pressure_rise_fraction", (dp > 0).mean()),
        ("active_fraction", (area > 0).mean()),
        ("centroid_dx_mean", dx.mean()), ("centroid_dy_mean", dy.mean()),
        ("direction_right_ratio", (dx > 0).mean()),
        ("direction_left_ratio", (dx < 0).mean()),
        ("direction_down_ratio", (dy > 0).mean()),
        ("direction_up_ratio", (dy < 0).mean()),
        ("direction_reversal_x", (np.diff(np.sign(dx)) != 0).mean() if dx.size > 1 else 0),
        ("direction_reversal_y", (np.diff(np.sign(dy)) != 0).mean() if dy.size > 1 else 0),
        ("poll_dt_mean", dt.mean() if dt.size else 0),
        ("poll_dt_std", dt.std() if dt.size else 0),
    ):
        names.append(name)
        values.append(float(value))
    result = np.nan_to_num(np.asarray(values), nan=0.0, posinf=0.0, neginf=0.0)
    return result, names


def segment_touch_event(matrix: np.ndarray, timestamps_ms: np.ndarray, gap_ms: float = 100.0, pad_ms: float = 100.0):
    """Return the padded longest active run using a baseline-relative peak threshold."""
    timestamps_ms = np.asarray(timestamps_ms, dtype=float)
    peak = np.maximum(np.asarray(matrix, dtype=float), 0).max(axis=(1, 2))
    baseline = peak[timestamps_ms <= min(200.0, float(timestamps_ms[-1]))]
    threshold = max(3.0, float(np.median(baseline)) + 2.0)
    active = peak >= threshold
    true_indices = np.flatnonzero(active)
    if not true_indices.size:
        return matrix, timestamps_ms - timestamps_ms[0], {"found": False, "threshold": threshold}
    # Bridge only short inactive gaps bounded by active samples.
    for left, right in zip(true_indices[:-1], true_indices[1:]):
        if right > left + 1 and timestamps_ms[right] - timestamps_ms[left] <= gap_ms:
            active[left : right + 1] = True
    runs, start = [], None
    for index, value in enumerate(active):
        if value and start is None:
            start = index
        if start is not None and (not value or index == len(active) - 1):
            end = index if value and index == len(active) - 1 else index - 1
            runs.append((start, end)); start = None
    start, end = max(runs, key=lambda run: timestamps_ms[run[1]] - timestamps_ms[run[0]])
    padded_start = int(np.searchsorted(timestamps_ms, timestamps_ms[start] - pad_ms, side="left"))
    padded_end = int(np.searchsorted(timestamps_ms, timestamps_ms[end] + pad_ms, side="right"))
    selected_t = timestamps_ms[padded_start:padded_end]
    info = {"found": True, "threshold": threshold, "start_ms": float(timestamps_ms[start]),
            "end_ms": float(timestamps_ms[end]), "padded_start_ms": float(selected_t[0]),
            "padded_end_ms": float(selected_t[-1])}
    return matrix[padded_start:padded_end], selected_t - selected_t[0], info


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_trial(raw_root: Path, row: dict[str, str]) -> tuple[np.ndarray, np.ndarray]:
    with np.load(raw_root / row["trial_path"] / "matrix.npz", allow_pickle=False) as archive:
        return archive["matrix"], archive["timestamps_ms"]


def augmented_rows(rows, raw_root: Path, policy: str, feature_cache=None, trial_cache=None, segment_events=False):
    if policy not in AUGMENTATIONS:
        raise ValueError(f"unknown augmentation policy: {policy}")
    feature_cache = {} if feature_cache is None else feature_cache
    trial_cache = {} if trial_cache is None else trial_cache
    features, labels, origins, names = [], [], [], None
    for row in rows:
        trial_key = row["trial_path"]
        if trial_key not in trial_cache:
            trial_cache[trial_key] = load_trial(raw_root, row)
        matrix, timestamps = trial_cache[trial_key]
        if segment_events:
            matrix, timestamps, _ = segment_touch_event(matrix, timestamps)
        for transform in AUGMENTATIONS[policy]:
            feature_key = (trial_key, transform, segment_events)
            if feature_key not in feature_cache:
                feature_cache[feature_key] = extract_features(transform_matrix(matrix, transform), timestamps)
            feature, current_names = feature_cache[feature_key]
            names = names or current_names
            features.append(feature)
            labels.append(row["verified_label"])
            origins.append((row["operator_id"], row["session_id"], row["planned_trial_id"], transform))
    return np.vstack(features), np.asarray(labels), origins, names
