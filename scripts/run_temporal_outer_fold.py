#!/usr/bin/env python3
"""Run one leakage-safe outer-operator fold for the exploratory TCN."""

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
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from deepskin_temporal.model import SmallTCN
from train_temporal_tcn import LABELS, load_operator

OPERATORS = ["operator_01", "operator_02", "operator_03"]
V1_FOLD_MACRO_F1 = {
    "operator_01": 0.8745373418184478,
    "operator_02": 0.9061058906321149,
    "operator_03": 0.7800592684626297,
}


def seed_everything(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def combine(cache: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]], operators: list[str]):
    return tuple(np.concatenate([cache[operator][index] for operator in operators], axis=0)
                 for index in range(3))


def normalize(train_x, train_m, other_x):
    mean = train_x[train_m.astype(bool)].mean(axis=0)
    std = train_x[train_m.astype(bool)].std(axis=0).clip(min=1e-5)
    train_scaled = ((train_x - mean) / std) * train_m[..., None]
    other_scaled = [((item[0] - mean) / std) * item[1][..., None] for item in other_x]
    return train_scaled.astype(np.float32), [x.astype(np.float32) for x in other_scaled], mean, std


def predict(model, x, mask, device):
    model.eval()
    with torch.no_grad():
        return model(torch.from_numpy(x).to(device), torch.from_numpy(mask).to(device)).argmax(1).cpu().numpy()


def train_curve(train_data, validation_data, *, epochs: int, seed: int, device, input_channels: int):
    train_x, train_m, train_y = train_data
    val_x, val_m, val_y = validation_data
    train_x, [val_x], mean, std = normalize(train_x, train_m, [(val_x, val_m)])
    seed_everything(seed)
    loader = DataLoader(TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_m),
                                      torch.from_numpy(train_y)), batch_size=16, shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    model = SmallTCN(input_channels=input_channels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    history = []
    for epoch in range(1, epochs + 1):
        model.train(); losses = []
        for sequence, mask, labels in loader:
            sequence, mask, labels = sequence.to(device), mask.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(sequence, mask), labels)
            if not torch.isfinite(loss): raise FloatingPointError("non-finite loss")
            loss.backward()
            if not all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()):
                raise FloatingPointError("non-finite gradient")
            optimizer.step(); losses.append(float(loss.detach()))
        prediction = predict(model, val_x, val_m, device)
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)),
                        "validation_macro_f1": float(f1_score(val_y, prediction, labels=range(7),
                                                               average="macro", zero_division=0))})
    return history, mean, std


def fit_fixed_epochs(train_data, test_data, *, epochs: int, seed: int, device, input_channels: int):
    train_x, train_m, train_y = train_data
    test_x, test_m, test_y = test_data
    train_x, [test_x], mean, std = normalize(train_x, train_m, [(test_x, test_m)])
    seed_everything(seed)
    loader = DataLoader(TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_m),
                                      torch.from_numpy(train_y)), batch_size=16, shuffle=True,
                        generator=torch.Generator().manual_seed(seed))
    model = SmallTCN(input_channels=input_channels).to(device); optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    loss_fn = nn.CrossEntropyLoss(); losses = []
    for _ in range(epochs):
        model.train(); epoch_losses = []
        for sequence, mask, labels in loader:
            sequence, mask, labels = sequence.to(device), mask.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True); loss = loss_fn(model(sequence, mask), labels)
            if not torch.isfinite(loss): raise FloatingPointError("non-finite final loss")
            loss.backward(); optimizer.step(); epoch_losses.append(float(loss.detach()))
        losses.append(float(np.mean(epoch_losses)))
    return model, predict(model, test_x, test_m, device), mean, std, losses


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "models/deepskin_social_touch_v2/training_manifest.csv")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/raw/deepskin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-epochs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260824)
    parser.add_argument("--outer-test-operator", choices=OPERATORS, default="operator_03")
    parser.add_argument("--feature-version", choices=["v1", "v2"], default="v1")
    parser.add_argument("--smoke", action="store_true", help="Run inner folds only; never load outer-test arrays")
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(f"refusing to overwrite run: {args.output}")
    if not 1 <= args.max_epochs <= 100: parser.error("max epochs must be in [1,100]")
    if not torch.cuda.is_available(): raise RuntimeError("CUDA is required")
    args.output.mkdir(parents=True)
    rows = list(csv.DictReader(args.manifest.open(encoding="utf-8", newline="")))
    device = torch.device("cuda"); started = time.perf_counter(); torch.cuda.reset_peak_memory_stats()
    inner_operators = [operator for operator in OPERATORS if operator != args.outer_test_operator]
    cache = {operator: load_operator(rows, operator, args.raw_root, args.feature_version) for operator in inner_operators}
    input_channels = int(next(iter(cache.values()))[0].shape[2])
    inner_specs = [(inner_operators[0], inner_operators[1]), (inner_operators[1], inner_operators[0])]
    histories = []
    for index, (train_operator, validation_operator) in enumerate(inner_specs):
        history, _, _ = train_curve(cache[train_operator], cache[validation_operator],
                                    epochs=args.max_epochs, seed=args.seed + index, device=device,
                                    input_channels=input_channels)
        histories.append({"train_operator": train_operator, "validation_operator": validation_operator,
                          "history": history})
    mean_scores = [float(np.mean([fold["history"][epoch]["validation_macro_f1"] for fold in histories]))
                   for epoch in range(args.max_epochs)]
    selected_epochs = int(np.argmax(mean_scores)) + 1
    base_report = {"schema_version": "deepskin-temporal-outer-fold-v1", "seed": args.seed,
                   "outer_test_operator": args.outer_test_operator, "inner_folds": histories,
                   "selected_epochs": selected_epochs, "selected_inner_mean_macro_f1": mean_scores[selected_epochs - 1],
                   "model_parameters": sum(p.numel() for p in SmallTCN(input_channels=input_channels).parameters()),
                   "feature_version": args.feature_version, "input_channels": input_channels,
                   "device": torch.cuda.get_device_name(0), "max_epochs": args.max_epochs}
    if args.smoke:
        base_report.update({"smoke_passed": True, "outer_test_loaded": False,
                            "elapsed_seconds": time.perf_counter() - started, "performance_claim": False})
        (args.output / "report.json").write_text(json.dumps(base_report, indent=2), encoding="utf-8")
        print(json.dumps(base_report, indent=2)); return 0

    cache[args.outer_test_operator] = load_operator(rows, args.outer_test_operator, args.raw_root, args.feature_version)
    train_data = combine(cache, inner_operators)
    model, prediction, mean, std, final_losses = fit_fixed_epochs(
        train_data, cache[args.outer_test_operator], epochs=selected_epochs, seed=args.seed, device=device,
        input_channels=input_channels)
    true = cache[args.outer_test_operator][2]
    matrix = confusion_matrix(true, prediction, labels=range(7))
    per_class = f1_score(true, prediction, labels=range(7), average=None, zero_division=0)
    metrics = {"rows": int(len(true)), "macro_f1": float(f1_score(true, prediction, labels=range(7), average="macro")),
               "balanced_accuracy": float(balanced_accuracy_score(true, prediction)),
               "accuracy": float(accuracy_score(true, prediction)),
               "per_class_f1": {label: float(value) for label, value in zip(LABELS, per_class)},
               "confusion_matrix": matrix.tolist(), "label_order": LABELS,
               "v1_same_fold_macro_f1_reference": V1_FOLD_MACRO_F1[args.outer_test_operator]}
    torch.cuda.synchronize()
    base_report.update({"outer_train_operators": inner_operators,
                        "outer_train_rows": int(len(train_data[2])), "outer_test_rows": int(len(true)),
                        "final_train_loss": final_losses[-1], "metrics": metrics,
                        "elapsed_seconds": time.perf_counter() - started,
                        "peak_cuda_memory_mb": torch.cuda.max_memory_allocated() / 1024 / 1024,
                        "performance_claim_scope": "single outer operator fold only"})
    torch.save({"model_state": model.state_dict(), "channel_mean": mean, "channel_std": std,
                "labels": LABELS, "selected_epochs": selected_epochs, "seed": args.seed},
               args.output / f"model_{args.outer_test_operator}.pt")
    with (args.output / "predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["row", "true_label", "predicted_label"])
        writer.writerows((index, LABELS[t], LABELS[p]) for index, (t, p) in enumerate(zip(true, prediction)))
    (args.output / "report.json").write_text(json.dumps(base_report, indent=2), encoding="utf-8")
    print(json.dumps(base_report, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
