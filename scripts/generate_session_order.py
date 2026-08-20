#!/usr/bin/env python3
"""Generate one deterministic, balanced, non-overwriting session order."""

from __future__ import annotations

import argparse
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GESTURES = ("TAP", "POKE", "STATIC_TOUCH", "STROKE", "RUB", "PAT", "IMPACT")


def has_long_run(labels: list[str], maximum: int = 2) -> bool:
    return any(len(set(labels[index : index + maximum + 1])) == 1 for index in range(len(labels) - maximum))


def generate_labels(seed: int) -> list[str]:
    rng = random.Random(seed)
    base = [gesture for gesture in GESTURES for _ in range(5)]
    for _ in range(10000):
        labels = base.copy()
        rng.shuffle(labels)
        if not has_long_run(labels):
            return labels
    raise RuntimeError("could not generate a valid session order")


def read_variations(path: Path) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            grouped[row["gesture"]].append(row)
    missing = [gesture for gesture in GESTURES if not grouped[gesture]]
    if missing:
        raise ValueError(f"variation schedule missing gestures: {missing}")
    return grouped


def write_order(operator_id: str, session_id: str, seed: int, schedule: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite session order: {output}")
    labels = generate_labels(seed)
    if Counter(labels) != Counter({gesture: 5 for gesture in GESTURES}):
        raise AssertionError("generated order is not balanced")
    variations = read_variations(schedule)
    used: Counter[str] = Counter()
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "sequence",
        "trial_id",
        "operator_id",
        "session_id",
        "seed",
        "instruction_label",
        "intensity",
        "speed",
        "direction",
        "position",
        "contact_style",
        "pulse_count",
        "notes",
    )
    with output.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for sequence, label in enumerate(labels, start=1):
            candidates = variations[label]
            variation = candidates[used[label] % len(candidates)]
            used[label] += 1
            writer.writerow(
                {
                    "sequence": sequence,
                    "trial_id": f"trial_{sequence:06d}",
                    "operator_id": operator_id,
                    "session_id": session_id,
                    "seed": seed,
                    "instruction_label": label,
                    **{field: variation.get(field, "") for field in fields[6:]},
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--schedule", type=Path, default=REPO_ROOT / "protocol" / "gesture_variation_schedule.csv")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (
        REPO_ROOT / "protocol" / "session_orders" / f"{args.operator_id}_{args.session_id}.csv"
    )
    write_order(args.operator_id, args.session_id, args.seed, args.schedule, output)
    print(f"Saved 35-trial order: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
