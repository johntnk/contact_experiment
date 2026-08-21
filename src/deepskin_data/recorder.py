"""Safe, atomic recording and validation of one controlled trial."""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .schema import TrialMetadata


def validate_arrays(
    matrix: np.ndarray,
    timestamps_ms: np.ndarray,
    frame_ids: np.ndarray,
    touch_state: np.ndarray,
) -> None:
    if matrix.ndim != 3:
        raise ValueError("matrix must have shape [T, rows, cols]")
    frame_count = matrix.shape[0]
    if frame_count <= 0:
        raise ValueError("trial contains no frames")
    for name, values in (
        ("timestamps_ms", timestamps_ms),
        ("frame_ids", frame_ids),
        ("touch_state", touch_state),
    ):
        if values.shape != (frame_count,):
            raise ValueError(f"{name} must have shape [{frame_count}]")
    if np.any(np.diff(timestamps_ms) < 0):
        raise ValueError("timestamps_ms must be monotonic")
    if not np.array_equal(frame_ids, np.arange(frame_count, dtype=frame_ids.dtype)):
        raise ValueError("frame_ids must be contiguous host-generated IDs from zero")


def collect_frames(
    sdk: Any,
    duration_s: float,
    poll_interval_ms: float,
    clock_ns: Callable[[], int] = time.monotonic_ns,
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    if duration_s <= 0 or poll_interval_ms < 0:
        raise ValueError("invalid recording duration or poll interval")
    rows, cols = sdk.matrix_size()
    buffer = sdk.allocate_matrix(rows, cols)
    matrices: list[list[float]] = []
    timestamps: list[float] = []
    touches: list[bool] = []
    events: list[dict[str, Any]] = []
    start_ns = clock_ns()
    deadline_ns = start_ns + int(duration_s * 1_000_000_000)
    while clock_ns() < deadline_ns:
        sdk.read_matrix(buffer)
        now_ns = clock_ns()
        frame_id = len(matrices)
        timestamp_ms = (now_ns - start_ns) / 1_000_000
        matrices.append(list(buffer))
        timestamps.append(timestamp_ms)
        touches.append(bool(sdk.is_touching()))
        try:
            raw_json = sdk.current_json()
            payload: Any = json.loads(raw_json)
            events.append({"frame_id": frame_id, "timestamp_ms": timestamp_ms, "payload": payload})
        except Exception as exc:
            events.append({"frame_id": frame_id, "timestamp_ms": timestamp_ms, "error": str(exc)})
        if poll_interval_ms:
            time.sleep(poll_interval_ms / 1000)
    matrix = np.asarray(matrices, dtype=np.float64).reshape((-1, rows, cols))
    arrays = {
        "matrix": matrix,
        "timestamps_ms": np.asarray(timestamps, dtype=np.float64),
        "frame_ids": np.arange(len(matrices), dtype=np.int64),
        "touch_state": np.asarray(touches, dtype=np.bool_),
    }
    validate_arrays(**arrays)
    return arrays, events


def write_trial_atomic(
    raw_root: Path,
    metadata: TrialMetadata,
    arrays: dict[str, np.ndarray],
    sdk_events: list[dict[str, Any]],
) -> Path:
    metadata.validate()
    validate_arrays(**arrays)
    if arrays["matrix"].shape[1:] != (metadata.matrix_rows, metadata.matrix_cols):
        raise ValueError("matrix shape disagrees with metadata")
    if arrays["matrix"].shape[0] != metadata.frame_count:
        raise ValueError("frame_count disagrees with metadata")
    target = raw_root / metadata.operator_id / metadata.session_id / metadata.trial_id
    if target.exists():
        raise FileExistsError(f"refusing to overwrite raw trial: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".{target.name}.tmp-{uuid.uuid4().hex}"
    temporary.mkdir()
    try:
        with (temporary / "matrix.npz").open("wb") as handle:
            np.savez_compressed(handle, **arrays)
        (temporary / "metadata.json").write_text(
            json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with (temporary / "sdk_events.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
            for event in sdk_events:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        validate_trial_directory(temporary)
        os.replace(temporary, target)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return target


def validate_trial_directory(path: Path) -> TrialMetadata:
    required = ("matrix.npz", "metadata.json", "sdk_events.jsonl")
    missing = [name for name in required if not (path / name).is_file()]
    if missing:
        raise ValueError(f"trial is missing files: {', '.join(missing)}")
    payload = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    metadata = TrialMetadata(**payload)
    metadata.validate()
    with np.load(path / "matrix.npz", allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ("matrix", "timestamps_ms", "frame_ids", "touch_state")}
    validate_arrays(**arrays)
    if arrays["matrix"].shape != (
        metadata.frame_count,
        metadata.matrix_rows,
        metadata.matrix_cols,
    ):
        raise ValueError("matrix.npz shape disagrees with metadata")
    return metadata


def summarize_trial(path: Path) -> dict[str, Any]:
    metadata = validate_trial_directory(path)
    with np.load(path / "matrix.npz", allow_pickle=False) as archive:
        matrix = archive["matrix"]
        timestamps = archive["timestamps_ms"]
        touch_state = archive["touch_state"]
    changed = int(np.count_nonzero(np.any(np.diff(matrix, axis=0) != 0, axis=(1, 2))))
    return {
        "schema_version": metadata.schema_version,
        "trial_id": metadata.trial_id,
        "status": metadata.trial_status,
        "verified_label": metadata.verified_label,
        "matrix_shape": list(matrix.shape),
        "duration_ms": float(timestamps[-1]) if len(timestamps) else 0.0,
        "changed_frame_transitions": changed,
        "touch_true_frames": int(np.count_nonzero(touch_state)),
        "value_min": float(matrix.min()),
        "value_max": float(matrix.max()),
    }


def finalize_metadata(metadata: TrialMetadata, arrays: dict[str, np.ndarray]) -> TrialMetadata:
    duration_ms = float(arrays["timestamps_ms"][-1]) if len(arrays["timestamps_ms"]) else 0.0
    frame_count = int(arrays["matrix"].shape[0])
    duration_s = max(duration_ms / 1000, 1e-9)
    changed_transitions = int(
        np.count_nonzero(np.any(np.diff(arrays["matrix"], axis=0) != 0, axis=(1, 2)))
    )
    observed_hz = (changed_transitions + 1) / duration_s
    host_poll_rate_hz = frame_count / duration_s
    return replace(
        metadata,
        frame_count=frame_count,
        duration_ms=duration_ms,
        sampling_rate_observed_hz=observed_hz,
        host_poll_rate_hz=host_poll_rate_hz,
    )
