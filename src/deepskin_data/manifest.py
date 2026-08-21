"""Build a deterministic Gold manifest from validated immutable trials."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from .recorder import summarize_trial, validate_trial_directory
from .recollection import load_recollection_plan


FIELDS = (
    "trial_path",
    "operator_id",
    "session_id",
    "trial_id",
    "planned_trial_id",
    "attempt_no",
    "verified_label",
    "trial_status",
    "intensity_instruction",
    "speed_instruction",
    "direction_instruction",
    "position_instruction",
    "sampling_rate_observed_hz",
    "frame_count",
    "duration_ms",
    "quality_flags",
)


def build_gold_manifest(raw_root: Path, output: Path, recollection_plan: Path | None = None) -> int:
    minimum_attempts = load_recollection_plan(recollection_plan)
    rows: list[dict[str, object]] = []
    for metadata_path in sorted(raw_root.glob("*/*/*/metadata.json")):
        trial_path = metadata_path.parent
        metadata = validate_trial_directory(trial_path)
        planned_trial_id = metadata.planned_trial_id or metadata.trial_id
        minimum_attempt = minimum_attempts.get(
            (metadata.operator_id, metadata.session_id, planned_trial_id), 1
        )
        if (
            metadata.trial_status != "VALID"
            or metadata.label_quality != "GOLD"
            or metadata.host_poll_rate_hz is None
            or metadata.attempt_no < minimum_attempt
        ):
            continue
        summary = summarize_trial(trial_path)
        quality_flags = []
        if summary["touch_true_frames"] == 0:
            quality_flags.append("SDK_TOUCH_FLAG_ALWAYS_FALSE")
        relative = trial_path.relative_to(raw_root).as_posix()
        rows.append(
            {
                "trial_path": relative,
                "operator_id": metadata.operator_id,
                "session_id": metadata.session_id,
                "trial_id": metadata.trial_id,
                "planned_trial_id": planned_trial_id,
                "attempt_no": metadata.attempt_no,
                "verified_label": metadata.verified_label,
                "trial_status": metadata.trial_status,
                "intensity_instruction": metadata.intensity_instruction or "",
                "speed_instruction": metadata.speed_instruction or "",
                "direction_instruction": metadata.direction_instruction or "",
                "position_instruction": metadata.position_instruction or "",
                "sampling_rate_observed_hz": f"{metadata.sampling_rate_observed_hz:.6f}",
                "frame_count": metadata.frame_count,
                "duration_ms": f"{metadata.duration_ms:.3f}",
                "quality_flags": ";".join(quality_flags),
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_name, output)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return len(rows)
