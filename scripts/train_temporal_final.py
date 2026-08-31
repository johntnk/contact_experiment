#!/usr/bin/env python3
"""Fit the frozen exploratory TCN on all 315 Gold trials for local runtime use."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from deepskin_temporal.model import SmallTCN
from train_temporal_tcn import LABELS, load_operator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "models/deepskin_social_touch_v2/training_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    parser.add_argument("--output", type=Path, default=ROOT / "models/deepskin_temporal_tcn_v1")
    parser.add_argument("--epochs", type=int, default=36)
    parser.add_argument("--seed", type=int, default=20260824)
    parser.add_argument("--feature-version", choices=["v1", "v2"], default="v1")
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(f"refusing to overwrite model package: {args.output}")
    args.output.mkdir(parents=True)
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed); torch.cuda.manual_seed_all(args.seed)
    torch.backends.cudnn.benchmark = False; torch.backends.cudnn.deterministic = True
    if not torch.cuda.is_available(): raise RuntimeError("CUDA is required for final TCN fit")
    rows = list(csv.DictReader(args.manifest.open(encoding="utf-8", newline="")))
    parts = [load_operator(rows, operator, args.raw_root, args.feature_version)
             for operator in ("operator_01", "operator_02", "operator_03")]
    x, mask, y = (np.concatenate([part[index] for part in parts]) for index in range(3))
    mean = x[mask.astype(bool)].mean(axis=0); std = x[mask.astype(bool)].std(axis=0).clip(min=1e-5)
    x = (((x - mean) / std) * mask[..., None]).astype(np.float32)
    loader = DataLoader(TensorDataset(torch.from_numpy(x), torch.from_numpy(mask), torch.from_numpy(y)),
                        batch_size=16, shuffle=True, generator=torch.Generator().manual_seed(args.seed))
    input_channels = int(x.shape[2])
    device = torch.device("cuda"); model = SmallTCN(input_channels=input_channels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3); loss_fn = nn.CrossEntropyLoss()
    losses = []
    for _ in range(args.epochs):
        model.train(); epoch_losses = []
        for sequence, valid, labels in loader:
            sequence, valid, labels = sequence.to(device), valid.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True); loss = loss_fn(model(sequence, valid), labels)
            if not torch.isfinite(loss): raise FloatingPointError("non-finite final TCN loss")
            loss.backward(); optimizer.step(); epoch_losses.append(float(loss.detach()))
        losses.append(float(np.mean(epoch_losses)))
    checkpoint = {"schema_version": "deepskin-temporal-tcn-runtime-v1", "model_state": model.state_dict(),
                  "channel_mean": mean, "channel_std": std, "labels": LABELS, "seed": args.seed,
                  "epochs": args.epochs, "input_channels": input_channels, "max_frames": 256,
                  "resample_hz": 50.0, "feature_version": args.feature_version}
    model_path = args.output / "model.pt"; torch.save(checkpoint, model_path)
    reloaded = torch.load(model_path, map_location=device, weights_only=False)
    check_model = SmallTCN(input_channels=input_channels).to(device)
    check_model.load_state_dict(reloaded["model_state"]); check_model.eval()
    with torch.no_grad(): check = check_model(torch.from_numpy(x[:2]).to(device), torch.from_numpy(mask[:2]).to(device))
    if check.shape != (2, 7) or not torch.isfinite(check).all(): raise RuntimeError("reloaded TCN verification failed")
    shutil.copyfile(args.manifest, args.output / "training_manifest.csv")
    oof = ({"macro_f1": 0.8888442477494133, "balanced_accuracy": 0.8888888888888891}
           if args.feature_version == "v2"
           else {"macro_f1": 0.8623461069886339, "balanced_accuracy": 0.8634920634920634})
    config = {"schema_version": "deepskin-temporal-runtime-config-v1", "training_recipe": "target_only_tcn_exploratory",
              "seed": args.seed, "epochs": args.epochs, "rows": int(len(y)), "parameters": sum(p.numel() for p in model.parameters()),
              "feature_version": args.feature_version, "input_channels": input_channels,
              "oof_macro_f1": oof["macro_f1"], "oof_balanced_accuracy": oof["balanced_accuracy"],
              "v1_replacement_gate_passed": False, "runtime_confidence_threshold_default": 0.50}
    (args.output / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (args.output / "labels.json").write_text(json.dumps(LABELS, indent=2), encoding="utf-8")
    sha = hashlib.sha256(model_path.read_bytes()).hexdigest()
    (args.output / "checksums.sha256").write_text(f"{sha}  model.pt\n", encoding="utf-8")
    report = {**config, "final_train_loss": losses[-1], "model_sha256": sha,
              "reload_verified": True, "performance_claim_source": "three-fold OOF, not full-data fit"}
    (args.output / "fit_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
