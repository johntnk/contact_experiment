"""Label stabilization for causal streaming recognition."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


SUSTAINED_REALTIME_LABELS = frozenset({"RUB", "STATIC_TOUCH", "STROKE"})


def is_sustained_realtime_label(label: str) -> bool:
    """Return whether a class is safe to emit from an incomplete causal window."""
    return label in SUSTAINED_REALTIME_LABELS


@dataclass(frozen=True)
class StabilizedLabel:
    current_label: str | None
    candidate_label: str | None
    candidate_count: int
    changed: bool
    state: str


class RealtimeLabelStabilizer:
    def __init__(self, *, confidence_threshold: float = 0.5,
                 initial_confirmations: int = 3, switch_confirmations: int = 2,
                 fast_initial_confirmations: dict[str, int] | None = None) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence threshold must be in [0,1]")
        if initial_confirmations < 1 or switch_confirmations < 1:
            raise ValueError("confirmation counts must be positive")
        self.confidence_threshold = float(confidence_threshold)
        self.initial_confirmations = int(initial_confirmations)
        self.switch_confirmations = int(switch_confirmations)
        self.fast_initial_confirmations = dict(fast_initial_confirmations or {})
        if any(value < 1 or value > self.initial_confirmations
               for value in self.fast_initial_confirmations.values()):
            raise ValueError("fast initial confirmations must be between 1 and the default")
        self.current_label: str | None = None
        self.candidate_label: str | None = None
        self.candidate_count = 0

    def reset(self) -> StabilizedLabel:
        self.current_label = None
        self.candidate_label = None
        self.candidate_count = 0
        return StabilizedLabel(None, None, 0, False, "idle")

    def update(self, label: str, confidence: float) -> StabilizedLabel:
        if confidence < self.confidence_threshold:
            self.candidate_label = None
            self.candidate_count = 0
            return StabilizedLabel(self.current_label, None, 0, False, "low_confidence")
        if label == self.current_label:
            self.candidate_label = None
            self.candidate_count = 0
            return StabilizedLabel(self.current_label, None, 0, False, "stable")
        if label == self.candidate_label:
            self.candidate_count += 1
        else:
            self.candidate_label = label
            self.candidate_count = 1
        required = (self.fast_initial_confirmations.get(label, self.initial_confirmations)
                    if self.current_label is None else self.switch_confirmations)
        if self.candidate_count < required:
            return StabilizedLabel(self.current_label, self.candidate_label,
                                   self.candidate_count, False, "confirming")
        self.current_label = label
        self.candidate_label = None
        self.candidate_count = 0
        return StabilizedLabel(self.current_label, None, 0, True, "switched")


def summarize_inference_times(values_ms, budget_ms: float) -> dict[str, float | int]:
    """Summarize a bounded latency window against the configured update budget."""
    values = np.asarray(list(values_ms), dtype=np.float64)
    if values.ndim != 1 or not values.size or not np.isfinite(values).all():
        raise ValueError("inference timings must be a non-empty finite sequence")
    return {
        "samples": int(values.size),
        "mean_ms": float(values.mean()),
        "p95_ms": float(np.percentile(values, 95)),
        "max_ms": float(values.max()),
        "recent_overruns": int(np.count_nonzero(values > float(budget_ms))),
    }
