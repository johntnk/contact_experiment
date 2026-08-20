"""Frozen stage 2 trial metadata contract and validation."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


SCHEMA_VERSION = "deepskin-trial-v1"
GESTURE_LABELS = (
    "TAP",
    "POKE",
    "STATIC_TOUCH",
    "STROKE",
    "RUB",
    "PAT",
    "IMPACT",
)
TRIAL_STATUSES = ("VALID", "REDO", "UNCERTAIN")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class TrialMetadata:
    operator_id: str
    session_id: str
    trial_id: str
    instruction_label: str
    verified_label: str | None
    trial_status: str
    intensity_instruction: str | None
    speed_instruction: str | None
    direction_instruction: str | None
    position_instruction: str | None
    contact_style_instruction: str | None
    pulse_count_instruction: int | None
    device_model: str
    matrix_rows: int
    matrix_cols: int
    sampling_rate_observed_hz: float
    recorded_at: str
    frame_count: int
    duration_ms: float
    notes: str = ""
    schema_version: str = SCHEMA_VERSION
    label_source: str | None = None
    label_quality: str | None = None
    sdk_version: str = "unknown"
    timestamp_source: str = "host_monotonic"
    frame_id_source: str = "host_generated"
    host_poll_rate_hz: float | None = None

    def validate(self) -> None:
        for field_name in ("operator_id", "session_id", "trial_id"):
            value = getattr(self, field_name)
            if not _SAFE_ID.fullmatch(value):
                raise ValueError(f"invalid {field_name}: {value!r}")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version: {self.schema_version}")
        if self.instruction_label not in GESTURE_LABELS:
            raise ValueError(f"invalid instruction_label: {self.instruction_label}")
        if self.trial_status not in TRIAL_STATUSES:
            raise ValueError(f"invalid trial_status: {self.trial_status}")
        if self.trial_status == "VALID":
            if self.verified_label not in GESTURE_LABELS:
                raise ValueError("VALID requires an explicit seven-class verified_label")
            if self.label_source != "CONTROLLED_CONFIRMED" or self.label_quality != "GOLD":
                raise ValueError("VALID requires CONTROLLED_CONFIRMED/GOLD labels")
        elif self.verified_label is not None:
            raise ValueError(f"{self.trial_status} requires verified_label=null")
        if self.matrix_rows <= 0 or self.matrix_cols <= 0 or self.frame_count <= 0:
            raise ValueError("matrix dimensions and frame_count must be positive")
        if self.duration_ms < 0 or self.sampling_rate_observed_hz <= 0:
            raise ValueError("duration and sampling rate are invalid")
        if self.host_poll_rate_hz is not None and self.host_poll_rate_hz <= 0:
            raise ValueError("host_poll_rate_hz must be positive")
        if self.pulse_count_instruction is not None and self.pulse_count_instruction <= 0:
            raise ValueError("pulse_count_instruction must be positive")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
