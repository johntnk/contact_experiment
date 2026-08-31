#!/usr/bin/env python3
"""Fit a personalized TCN using Gold plus frozen natural PAT/RUB adaptation data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import confusion_matrix
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from audit_live_pat_rub_tcn import runtime_event
from deepskin_temporal.model import SmallTCN
from deepskin_temporal.sequence import extract_event_sequence, extract_event_sequence_v2
from train_temporal_tcn import LABELS, load_operator


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def load_live(directory: Path, feature_version: str):
    extractor = extract_event_sequence if feature_version == "v1" else extract_event_sequence_v2
    by_label = {"PAT": [], "RUB": []}
    excluded = []
    for metadata_path in sorted(directory.glob("*.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        label = str(metadata["expected_label"])
        if label not in by_label:
            continue
        raw_path = metadata_path.with_suffix(".npz")
        with np.load(raw_path, allow_pickle=False) as archive:
            matrix = archive["matrix"]
            timestamps = archive["timestamps_ms"]
        try:
            event = runtime_event(matrix, timestamps)
        except ValueError as exc:
            excluded.append({"capture": metadata_path.stem, "label": label, "reason": str(exc)})
            continue
        sequence, mask = extractor(event.matrix, event.timestamps_ms, baseline_window_ms=75.0)
        by_label[label].append((metadata_path.stem, sequence, mask, LABELS.index(label)))
    if any(len(by_label[label]) != 14 for label in by_label):
        raise ValueError(f"expected 14 usable captures per class, got { {k: len(v) for k, v in by_label.items()} }")
    train = by_label["PAT"][:10] + by_label["RUB"][:10]
    validation = by_label["PAT"][10:] + by_label["RUB"][10:]
    return train, validation, excluded


def stack(items):
    return (
        np.stack([item[1] for item in items]),
        np.stack([item[2] for item in items]),
        np.asarray([item[3] for item in items], dtype=np.int64),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adaptation-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--feature-version", choices=["v1", "v2"], default="v1")
    parser.add_argument("--adaptation-repeat", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=36)
    parser.add_argument("--seed", type=int, default=20260824)
    parser.add_argument("--manifest", type=Path, default=ROOT / "models/deepskin_social_touch_v2/training_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite adapted run: {args.output}")
    if not 1 <= args.epochs <= 100 or not 1 <= args.adaptation_repeat <= 20:
        parser.error("epochs must be 1..100 and adaptation-repeat must be 1..20")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    args.output.mkdir(parents=True)

    seed_everything(args.seed)
    rows = list(csv.DictReader(args.manifest.open(encoding="utf-8", newline="")))
    gold_parts = [load_operator(rows, operator, args.raw_root, args.feature_version)
                  for operator in ("operator_01", "operator_02", "operator_03")]
    gold_x, gold_m, gold_y = (np.concatenate([part[index] for part in gold_parts]) for index in range(3))
    live_train_items, live_validation_items, excluded = load_live(args.adaptation_dir, args.feature_version)
    live_x, live_m, live_y = stack(live_train_items)
    val_x, val_m, val_y = stack(live_validation_items)
    train_x = np.concatenate([gold_x, np.repeat(live_x, args.adaptation_repeat, axis=0)])
    train_m = np.concatenate([gold_m, np.repeat(live_m, args.adaptation_repeat, axis=0)])
    train_y = np.concatenate([gold_y, np.repeat(live_y, args.adaptation_repeat, axis=0)])
    mean = train_x[train_m.astype(bool)].mean(axis=0)
    std = train_x[train_m.astype(bool)].std(axis=0).clip(min=1e-5)
    train_x = (((train_x - mean) / std) * train_m[..., None]).astype(np.float32)
    val_x = (((val_x - mean) / std) * val_m[..., None]).astype(np.float32)

    loader = DataLoader(
        TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_m), torch.from_numpy(train_y)),
        batch_size=16,
        shuffle=True,
        generator=torch.Generator().manual_seed(args.seed),
    )
    device = torch.device("cuda")
    input_channels = int(train_x.shape[2])
    model = SmallTCN(input_channels=input_channels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    losses = []
    for _ in range(args.epochs):
        model.train()
        epoch_losses = []
        for sequence, mask, labels in loader:
            sequence, mask, labels = sequence.to(device), mask.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(sequence, mask), labels)
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite adapted loss")
            loss.backward()
            if not all(parameter.grad is None or torch.isfinite(parameter.grad).all() for parameter in model.parameters()):
                raise FloatingPointError("non-finite adapted gradient")
            optimizer.step()
            epoch_losses.append(float(loss.detach()))
        losses.append(float(np.mean(epoch_losses)))

    model.eval()
    with torch.inference_mode():
        logits = model(torch.from_numpy(val_x).to(device), torch.from_numpy(val_m).to(device))
        probabilities = torch.softmax(logits, dim=1).cpu().numpy()
    prediction = probabilities.argmax(axis=1)
    matrix = confusion_matrix(val_y, prediction, labels=[LABELS.index("PAT"), LABELS.index("RUB")])
    split = {
        "training": [item[0] for item in live_train_items],
        "validation": [item[0] for item in live_validation_items],
        "excluded": excluded,
    }
    checkpoint = {
        "schema_version": "deepskin-temporal-adapted-v1",
        "model_state": model.state_dict(),
        "channel_mean": mean,
        "channel_std": std,
        "labels": LABELS,
        "seed": args.seed,
        "epochs": args.epochs,
        "feature_version": args.feature_version,
        "input_channels": input_channels,
        "adaptation_repeat": args.adaptation_repeat,
    }
    model_path = args.output / "model.pt"
    torch.save(checkpoint, model_path)
    report = {
        "schema_version": "deepskin-temporal-adaptation-report-v1",
        "seed": args.seed,
        "epochs": args.epochs,
        "feature_version": args.feature_version,
        "input_channels": input_channels,
        "adaptation_repeat": args.adaptation_repeat,
        "gold_rows": int(len(gold_y)),
        "natural_train_unique_rows": int(len(live_y)),
        "natural_validation_rows": int(len(val_y)),
        "fitted_rows_after_repeat": int(len(train_y)),
        "final_train_loss": losses[-1],
        "natural_validation_accuracy_development_only": float((prediction == val_y).mean()),
        "natural_validation_confusion_pat_rub": matrix.tolist(),
        "natural_validation_predictions": [
            {
                "capture": item[0],
                "true_label": LABELS[int(true)],
                "predicted_label": LABELS[int(predicted)],
                "confidence": float(probabilities[index, predicted]),
            }
            for index, (item, true, predicted) in enumerate(zip(live_validation_items, val_y, prediction))
        ],
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "performance_claim": "development split only; independent live acceptance still required",
    }
    (args.output / "split.json").write_text(json.dumps(split, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
