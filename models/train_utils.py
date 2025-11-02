"""Training utilities for hydrologic models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import torch
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset


@dataclass
class TrainingConfig:
    epochs: int = 10
    learning_rate: float = 1e-3
    weight_decay: float = 0.0
    device: str = "cpu"
    gradient_clip: float = 1.0


def train(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    config: TrainingConfig,
) -> List[float]:
    """Train a model and return epoch losses."""

    device = torch.device(config.device)
    model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    losses: List[float] = []

    for epoch in range(config.epochs):
        model.train()
        running_loss = 0.0
        for batch in dataloader:
            inputs, targets = batch
            inputs = inputs.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            predictions = model(inputs)
            loss = criterion(predictions, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip)
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)
        epoch_loss = running_loss / len(dataloader.dataset)
        losses.append(epoch_loss)
    return losses


def evaluate(model: nn.Module, dataloader: DataLoader, criterion: nn.Module, device: str = "cpu") -> float:
    device_t = torch.device(device)
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for inputs, targets in dataloader:
            inputs = inputs.to(device_t)
            targets = targets.to(device_t)
            predictions = model(inputs)
            loss = criterion(predictions, targets)
            total_loss += loss.item() * inputs.size(0)
    return total_loss / len(dataloader.dataset)


def save_model(model: nn.Module, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)


def load_model(model: nn.Module, path: Path, device: str = "cpu") -> nn.Module:
    state_dict = torch.load(path, map_location=device)
    model.load_state_dict(state_dict)
    return model


__all__ = ["TrainingConfig", "train", "evaluate", "save_model", "load_model"]
