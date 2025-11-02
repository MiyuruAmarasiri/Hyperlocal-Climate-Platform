"""LSTM-based hydrologic model definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import torch
from torch import nn


class HydrologicLSTM(nn.Module):
    """Sequence-to-sequence LSTM for streamflow prediction."""

    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.1):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.regressor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1),
        )
        self.hidden_size = hidden_size
        self.num_layers = num_layers

    def forward(self, inputs: torch.Tensor, hidden: Tuple[torch.Tensor, torch.Tensor] | None = None) -> torch.Tensor:
        if hidden is None:
            hidden = self._init_hidden(inputs.size(0), inputs.device)
        outputs, hidden = self.lstm(inputs, hidden)
        discharge = self.regressor(outputs)
        return discharge.squeeze(-1)

    def _init_hidden(self, batch_size: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        weight = next(self.parameters()).data
        h0 = weight.new_zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        c0 = weight.new_zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        return h0, c0


@dataclass
class LSTMConfig:
    input_size: int
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.1

    def build(self) -> HydrologicLSTM:
        return HydrologicLSTM(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
        )


__all__ = ["HydrologicLSTM", "LSTMConfig"]
