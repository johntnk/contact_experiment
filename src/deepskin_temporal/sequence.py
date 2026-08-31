"""Leakage-safe conversion from a Deepskin trial to a compact temporal sequence."""

from __future__ import annotations

import numpy as np


def extract_event_sequence(matrix: np.ndarray, timestamps_ms: np.ndarray, *, hz: float = 50.0,
                           max_frames: int = 256, baseline_window_ms: float = 200.0) -> tuple[np.ndarray, np.ndarray]:
    matrix = np.asarray(matrix, dtype=np.float32)
    timestamps = np.asarray(timestamps_ms, dtype=np.float64)
    if matrix.ndim != 3 or matrix.shape[1:] != (18, 29) or len(matrix) != len(timestamps):
        raise ValueError("expected matrix [T,18,29] and matching timestamps")
    if len(timestamps) < 2 or np.any(np.diff(timestamps) < 0) or not np.isfinite(matrix).all():
        raise ValueError("temporal trial must be finite with non-decreasing timestamps")
    if np.any(np.diff(timestamps) == 0):
        # Recorder timestamps are millisecond-quantized and all Gold trials
        # contain duplicate poll times. Keep the final observation per time.
        _, reverse_indices = np.unique(timestamps[::-1], return_index=True)
        keep = np.sort(len(timestamps) - 1 - reverse_indices)
        timestamps = timestamps[keep]
        matrix = matrix[keep]
    if len(timestamps) < 2:
        raise ValueError("temporal trial needs at least two unique timestamps")

    baseline_mask = timestamps <= min(float(baseline_window_ms), float(timestamps[-1]))
    corrected = matrix - np.median(matrix[baseline_mask], axis=0, keepdims=True)
    positive = np.maximum(corrected, 0.0)
    peak = positive.max(axis=(1, 2))
    threshold = max(3.0, float(np.median(peak[baseline_mask])) + 2.0)
    active = np.flatnonzero(peak >= threshold)
    if active.size:
        start_ms = max(float(timestamps[0]), float(timestamps[active[0]]) - 100.0)
        end_ms = min(float(timestamps[-1]), float(timestamps[active[-1]]) + 100.0)
    else:
        start_ms, end_ms = float(timestamps[0]), float(timestamps[-1])

    target_t = np.arange(start_ms, end_ms + 0.5, 1000.0 / hz, dtype=np.float64)
    if len(target_t) > max_frames:
        center = len(target_t) // 2
        half = max_frames // 2
        target_t = target_t[center - half:center - half + max_frames]

    flat = positive.reshape(len(positive), -1)
    sampled = np.stack([np.interp(target_t, timestamps, flat[:, index])
                        for index in range(flat.shape[1])], axis=1).reshape(-1, 18, 29)
    total = sampled.sum(axis=(1, 2))
    maximum = sampled.max(axis=(1, 2))
    area = (sampled >= 3.0).mean(axis=(1, 2))
    yy, xx = np.mgrid[0:18, 0:29]
    denom = np.maximum(total, 1e-6)
    cx = (sampled * (xx / 28.0)).sum(axis=(1, 2)) / denom
    cy = (sampled * (yy / 17.0)).sum(axis=(1, 2)) / denom
    cx[total <= 1e-6] = 0.5
    cy[total <= 1e-6] = 0.5
    pooled = []
    for row_indices in np.array_split(np.arange(18), 4):
        for col_indices in np.array_split(np.arange(29), 4):
            pooled.append(sampled[:, row_indices][:, :, col_indices].mean(axis=(1, 2)))
    sequence = np.column_stack([total, maximum, area, cx, cy, *pooled]).astype(np.float32)
    output = np.zeros((max_frames, sequence.shape[1]), dtype=np.float32)
    mask = np.zeros(max_frames, dtype=np.float32)
    output[:len(sequence)] = sequence
    mask[:len(sequence)] = 1.0
    return output, mask


def extract_event_sequence_v2(matrix: np.ndarray, timestamps_ms: np.ndarray, *, hz: float = 50.0,
                              max_frames: int = 256, baseline_window_ms: float = 200.0) -> tuple[np.ndarray, np.ndarray]:
    """Add explicit contact, pressure-change, and centroid-motion channels."""
    base, mask = extract_event_sequence(
        matrix,
        timestamps_ms,
        hz=hz,
        max_frames=max_frames,
        baseline_window_ms=baseline_window_ms,
    )
    valid = int(mask.sum())
    output = np.zeros((max_frames, 27), dtype=np.float32)
    output[:, :21] = base
    if valid:
        sequence = base[:valid]
        total = sequence[:, 0]
        maximum = sequence[:, 1]
        cx = sequence[:, 3]
        cy = sequence[:, 4]
        d_total = np.diff(total, prepend=total[0])
        d_cx = np.diff(cx, prepend=cx[0])
        d_cy = np.diff(cy, prepend=cy[0])
        output[:valid, 21:] = np.column_stack(
            [maximum >= 3.0, d_total, np.abs(d_total), d_cx, d_cy, np.hypot(d_cx, d_cy)]
        )
    return output, mask


def extract_realtime_window(matrix: np.ndarray, timestamps_ms: np.ndarray, baseline: np.ndarray, *,
                            window_ms: float = 1500.0, hz: float = 50.0,
                            max_frames: int = 256) -> tuple[np.ndarray, np.ndarray]:
    """Convert the latest causal window using a fixed pre-contact baseline."""
    matrix = np.asarray(matrix, dtype=np.float32)
    timestamps = np.asarray(timestamps_ms, dtype=np.float64)
    baseline = np.asarray(baseline, dtype=np.float32)
    if matrix.ndim != 3 or matrix.shape[1:] != (18, 29) or baseline.shape != (18, 29):
        raise ValueError("expected matrix [T,18,29] and baseline [18,29]")
    if len(matrix) != len(timestamps) or len(timestamps) < 2 or np.any(np.diff(timestamps) < 0):
        raise ValueError("realtime window needs matching non-decreasing timestamps")
    if not np.isfinite(matrix).all() or not np.isfinite(baseline).all():
        raise ValueError("realtime window must be finite")
    if np.any(np.diff(timestamps) == 0):
        _, reverse_indices = np.unique(timestamps[::-1], return_index=True)
        keep = np.sort(len(timestamps) - 1 - reverse_indices)
        timestamps, matrix = timestamps[keep], matrix[keep]
    if len(timestamps) < 2:
        raise ValueError("realtime window needs two unique timestamps")
    start_ms = max(float(timestamps[0]), float(timestamps[-1]) - float(window_ms))
    start = int(np.searchsorted(timestamps, start_ms, side="left"))
    timestamps, matrix = timestamps[start:], matrix[start:]
    positive = np.maximum(matrix - baseline[None], 0.0)
    target_t = np.arange(float(timestamps[0]), float(timestamps[-1]) + 0.5, 1000.0 / hz)
    if len(target_t) > max_frames:
        target_t = target_t[-max_frames:]
    flat = positive.reshape(len(positive), -1)
    sampled = np.stack([np.interp(target_t, timestamps, flat[:, index])
                        for index in range(flat.shape[1])], axis=1).reshape(-1, 18, 29)
    total = sampled.sum(axis=(1, 2))
    maximum = sampled.max(axis=(1, 2))
    area = (sampled >= 3.0).mean(axis=(1, 2))
    yy, xx = np.mgrid[0:18, 0:29]
    denom = np.maximum(total, 1e-6)
    cx = (sampled * (xx / 28.0)).sum(axis=(1, 2)) / denom
    cy = (sampled * (yy / 17.0)).sum(axis=(1, 2)) / denom
    cx[total <= 1e-6] = 0.5
    cy[total <= 1e-6] = 0.5
    pooled = [sampled[:, rows][:, :, cols].mean(axis=(1, 2))
              for rows in np.array_split(np.arange(18), 4)
              for cols in np.array_split(np.arange(29), 4)]
    sequence = np.column_stack([total, maximum, area, cx, cy, *pooled]).astype(np.float32)
    output = np.zeros((max_frames, 21), dtype=np.float32)
    mask = np.zeros(max_frames, dtype=np.float32)
    output[:len(sequence)] = sequence
    mask[:len(sequence)] = 1.0
    return output, mask
