"""Positive-only acceptance gate for conservative target-class output."""

from __future__ import annotations

import numpy as np


def nearest_class_distance(
    scaled_feature: np.ndarray, references: dict[str, np.ndarray], predicted_label: str
) -> float:
    candidates = np.asarray(references[predicted_label], dtype=float)
    query = np.asarray(scaled_feature, dtype=float).reshape(1, -1)
    if candidates.ndim != 2 or candidates.shape[1] != query.shape[1]:
        raise ValueError("gate reference features have incompatible shape")
    return float(np.linalg.norm(candidates - query, axis=1).min())


def apply_positive_gate(
    scaled_feature: np.ndarray,
    predicted_label: str,
    gate: dict,
    event_found: bool = True,
) -> dict:
    if not event_found:
        return {"accepted": False, "output_label": "UNKNOWN", "reason": "no_touch_event", "distance": None, "threshold": None}
    distance = nearest_class_distance(scaled_feature, gate["references"], predicted_label)
    threshold = float(gate["thresholds"][predicted_label])
    accepted = bool(np.isfinite(distance) and distance <= threshold)
    return {
        "accepted": accepted,
        "output_label": predicted_label if accepted else "UNKNOWN",
        "reason": "accepted" if accepted else "outside_positive_region",
        "distance": distance,
        "threshold": threshold,
    }
