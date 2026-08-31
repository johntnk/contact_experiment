#!/usr/bin/env python3
"""Run a bounded GPU smoke for the exploratory V2 TCN."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_temporal.model import SmallTCN
from deepskin_temporal.sequence import extract_event_sequence, extract_event_sequence_v2

LABELS = ["IMPACT", "PAT", "POKE", "RUB", "STATIC_TOUCH", "STROKE", "TAP"]


def load_operator(rows: list[dict[str, str]], operator: str, raw_root: Path, feature_version: str = "v1"):
    extractor = extract_event_sequence if feature_version == "v1" else extract_event_sequence_v2
    sequences, masks, labels = [], [], []
    for row in rows:
        if row["operator_id"] != operator:
            continue
        with np.load(raw_root / row["trial_path"] / "matrix.npz", allow_pickle=False) as archive:
            sequence, mask = extractor(archive["matrix"], archive["timestamps_ms"])
        sequences.append(sequence); masks.append(mask); labels.append(LABELS.index(row["verified_label"]))
    return np.stack(sequences), np.stack(masks), np.asarray(labels, dtype=np.int64)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "models/deepskin_social_touch_v2/training_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260824)
    parser.add_argument("--feature-version", choices=["v1", "v2"], default="v1")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite temporal run: {args.output}")
    if args.epochs < 1 or args.epochs > 5:
        parser.error("smoke epochs must be between 1 and 5")
    args.output.mkdir(parents=True)

    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    if not torch.cuda.is_available():
        raise RuntimeError("V2 smoke requires CUDA")
    torch.cuda.manual_seed_all(args.seed)
    rows = list(csv.DictReader(args.manifest.open(encoding="utf-8", newline="")))
    train_x, train_m, train_y = load_operator(rows, "operator_01", args.raw_root, args.feature_version)
    val_x, val_m, val_y = load_operator(rows, "operator_02", args.raw_root, args.feature_version)

    mean = train_x[train_m.astype(bool)].mean(axis=0)
    std = train_x[train_m.astype(bool)].std(axis=0).clip(min=1e-5)
    train_x = ((train_x - mean) / std) * train_m[..., None]
    val_x = ((val_x - mean) / std) * val_m[..., None]
    loader = DataLoader(TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_m),
                                      torch.from_numpy(train_y)), batch_size=16, shuffle=True,
                        generator=torch.Generator().manual_seed(args.seed))
    device = torch.device("cuda")
    input_channels = int(train_x.shape[2])
    model = SmallTCN(input_channels=input_channels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    history, started = [], time.perf_counter()
    for epoch in range(args.epochs):
        model.train(); losses = []
        for sequence, mask, labels in loader:
            sequence, mask, labels = sequence.to(device), mask.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(sequence, mask), labels)
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite temporal loss")
            loss.backward()
            if not all(parameter.grad is None or torch.isfinite(parameter.grad).all() for parameter in model.parameters()):
                raise FloatingPointError("non-finite temporal gradient")
            optimizer.step(); losses.append(float(loss.detach()))
        model.eval()
        with torch.no_grad():
            logits = model(torch.from_numpy(val_x).to(device), torch.from_numpy(val_m).to(device))
            validation_accuracy = float((logits.argmax(1).cpu().numpy() == val_y).mean())
        history.append({"epoch": epoch + 1, "train_loss": float(np.mean(losses)),
                        "validation_accuracy_diagnostic_only": validation_accuracy})
    torch.cuda.synchronize()
    checkpoint = {"model_state": model.state_dict(), "channel_mean": mean, "channel_std": std,
                  "labels": LABELS, "seed": args.seed}
    torch.save(checkpoint, args.output / "model_smoke.pt")
    reloaded = SmallTCN(input_channels=input_channels).to(device)
    reloaded.load_state_dict(torch.load(args.output / "model_smoke.pt", weights_only=False)["model_state"])
    report = {"schema_version": "deepskin-temporal-smoke-v1", "seed": args.seed,
              "train_operator": "operator_01", "validation_operator": "operator_02",
              "held_out_operator_not_used": "operator_03", "epochs": args.epochs,
              "train_rows": int(len(train_y)), "validation_rows": int(len(val_y)),
              "model_parameters": int(sum(p.numel() for p in model.parameters())),
              "feature_version": args.feature_version, "input_channels": input_channels,
              "device": torch.cuda.get_device_name(0), "torch": torch.__version__,
              "cuda": torch.version.cuda, "elapsed_seconds": time.perf_counter() - started,
              "peak_cuda_memory_mb": torch.cuda.max_memory_allocated() / 1024 / 1024,
              "history": history, "smoke_passed": True,
              "performance_claim": False}
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
