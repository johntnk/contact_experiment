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


def extract_common_features(matrix: np.ndarray, timestamps_ms: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Extract sensor-shape-independent F0 features with normalized pressure/time/space."""
    raw = np.asarray(matrix, dtype=np.float64)
    timestamps_ms = np.asarray(timestamps_ms, dtype=np.float64)
    if raw.ndim != 3 or raw.shape[0] < 2 or len(timestamps_ms) != raw.shape[0]:
        raise ValueError("common features require matrix [T,H,W], T>=2, and matching timestamps")
    baseline_frames = max(1, min(raw.shape[0] // 10, int(np.searchsorted(timestamps_ms, 200.0, side="right"))))
    baseline = np.median(raw[:baseline_frames], axis=0)
    corrected = np.maximum(raw - baseline, 0.0)
    positive = corrected[corrected > 0]
    scale = float(np.percentile(positive, 99)) if positive.size else 1.0
    x = np.clip(corrected / max(scale, 1e-9), 0.0, 1.0)
    total = x.sum(axis=(1, 2))
    active = x > 0.05
    area = active.mean(axis=(1, 2))
    rows, cols = x.shape[1:]
    yy, xx = np.mgrid[0:rows, 0:cols]
    denom = total + 1e-12
    cx = (x * xx).sum(axis=(1, 2)) / denom / max(cols - 1, 1)
    cy = (x * yy).sum(axis=(1, 2)) / denom / max(rows - 1, 1)
    dx, dy = np.diff(cx), np.diff(cy)
    step = np.hypot(dx, dy)
    duration_s = max(float(timestamps_ms[-1] - timestamps_ms[0]) / 1000.0, 1e-9)
    values, names = [], []

    def add(name, value):
        names.append(name); values.append(float(value))

    for prefix, series in (("total_pressure_norm", total), ("contact_area_ratio", area)):
        for suffix, value in (("mean", series.mean()), ("std", series.std()), ("max", series.max()),
                              ("p50", np.percentile(series, 50)), ("p90", np.percentile(series, 90)),
                              ("p99", np.percentile(series, 99))):
            add(f"{prefix}_{suffix}", value)
    add("duration_s", duration_s)
    add("pressure_impulse_norm_s", np.trapezoid(total, timestamps_ms / 1000.0))
    add("centroid_x_start_norm", cx[0]); add("centroid_y_start_norm", cy[0])
    add("centroid_x_end_norm", cx[-1]); add("centroid_y_end_norm", cy[-1])
    add("centroid_displacement_norm", np.hypot(cx[-1] - cx[0], cy[-1] - cy[0]))
    add("trajectory_length_norm", step.sum()); add("movement_mean_norm", step.mean() if step.size else 0)
    add("movement_std_norm", step.std() if step.size else 0)
    add("sum_abs_dx_norm", np.abs(dx).sum()); add("sum_abs_dy_norm", np.abs(dy).sum())
    add("trajectory_straightness", np.hypot(cx[-1] - cx[0], cy[-1] - cy[0]) / max(step.sum(), 1e-9))
    add("mean_abs_temporal_derivative_per_s", np.abs(np.diff(total)).mean() * (raw.shape[0] - 1) / duration_s)
    row_edges = np.linspace(0, rows, 5, dtype=int)
    col_edges = np.linspace(0, cols, 5, dtype=int)
    for region_row in range(4):
        for region_col in range(4):
            block = x[:, row_edges[region_row]:row_edges[region_row + 1], col_edges[region_col]:col_edges[region_col + 1]]
            prefix = f"region_r{region_row}_c{region_col}"
            add(f"{prefix}_mean_pressure_norm", block.mean())
            add(f"{prefix}_max_pressure_norm", block.max())
            add(f"{prefix}_active_ratio", (block > 0.05).mean())
    return np.nan_to_num(np.asarray(values), nan=0.0, posinf=0.0, neginf=0.0), names


def domain_class_sample_weights(labels: np.ndarray, domains: np.ndarray, source_alpha: float) -> np.ndarray:
    """Balance classes within each domain and set source/target total-weight ratio to alpha."""
    labels = np.asarray(labels)
    domains = np.asarray(domains)
    if labels.ndim != 1 or domains.shape != labels.shape or labels.size == 0:
        raise ValueError("labels and domains must be matching non-empty 1D arrays")
    if source_alpha < 0:
        raise ValueError("source_alpha must be non-negative")
    unexpected = set(domains) - {"target", "source"}
    if unexpected or "target" not in set(domains):
        raise ValueError(f"domains must contain target and optionally source, got {sorted(set(domains))}")
    target_count = int(np.sum(domains == "target"))
    weights = np.zeros(labels.size, dtype=float)
    for domain, relative_total in (("target", 1.0), ("source", source_alpha)):
        mask = domains == domain
        if not np.any(mask):
            continue
        domain_labels = labels[mask]
        classes, counts = np.unique(domain_labels, return_counts=True)
        class_total = relative_total * target_count / len(classes)
        for label, count in zip(classes, counts):
            weights[mask & (labels == label)] = class_total / count
    return weights


def segment_touch_event(matrix: np.ndarray, timestamps_ms: np.ndarray, gap_ms: float = 100.0,
                        pad_ms: float = 100.0, baseline_window_ms: float = 200.0):
    """Return the padded longest active run using a baseline-relative peak threshold."""
    timestamps_ms = np.asarray(timestamps_ms, dtype=float)
    peak = np.maximum(np.asarray(matrix, dtype=float), 0).max(axis=(1, 2))
    baseline = peak[timestamps_ms <= min(float(baseline_window_ms), float(timestamps_ms[-1]))]
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
