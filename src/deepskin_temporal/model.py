"""Small residual TCN for exploratory seven-class sequence recognition."""

from __future__ import annotations

import torch
from torch import nn


class TemporalBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int, dilation: int) -> None:
        super().__init__()
        padding = dilation * (kernel_size - 1) // 2
        self.body = nn.Sequential(
            nn.Conv1d(in_channels, out_channels, kernel_size, padding=padding, dilation=dilation),
            nn.BatchNorm1d(out_channels), nn.ReLU(), nn.Dropout(0.15),
            nn.Conv1d(out_channels, out_channels, kernel_size, padding=padding, dilation=dilation),
            nn.BatchNorm1d(out_channels), nn.ReLU(),
        )
        self.skip = nn.Identity() if in_channels == out_channels else nn.Conv1d(in_channels, out_channels, 1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return torch.relu(self.body(inputs) + self.skip(inputs))


class SmallTCN(nn.Module):
    def __init__(self, input_channels: int = 21, classes: int = 7) -> None:
        super().__init__()
        self.blocks = nn.Sequential(
            TemporalBlock(input_channels, 32, 5, 1),
            TemporalBlock(32, 32, 5, 2),
            TemporalBlock(32, 64, 3, 4),
        )
        self.classifier = nn.Linear(128, classes)

    def forward(self, sequence: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        encoded = self.blocks(sequence.transpose(1, 2))
        expanded = mask.unsqueeze(1)
        mean = (encoded * expanded).sum(dim=2) / expanded.sum(dim=2).clamp_min(1.0)
        maximum = encoded.masked_fill(expanded == 0, float("-inf")).amax(dim=2)
        maximum = torch.where(torch.isfinite(maximum), maximum, torch.zeros_like(maximum))
        return self.classifier(torch.cat([mean, maximum], dim=1))
