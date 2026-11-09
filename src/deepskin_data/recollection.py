"""Load auditable minimum-attempt overrides for protocol-driven recollection."""

from __future__ import annotations

import csv
from pathlib import Path


RecollectionKey = tuple[str, str, str]


def load_recollection_plan(path: Path | None) -> dict[RecollectionKey, int]:
    if path is None or not path.exists():
        return {}
    result: dict[RecollectionKey, int] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["operator_id"], row["session_id"], row["planned_trial_id"])
            if key in result:
                raise ValueError(f"duplicate recollection key: {key}")
            minimum = int(row["minimum_attempt_no"])
            if minimum < 2:
                raise ValueError(f"minimum_attempt_no must be at least 2: {key}")
            result[key] = minimum
    return result
