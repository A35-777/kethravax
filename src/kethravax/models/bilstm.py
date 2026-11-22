"""Bidirectional LSTM neural baseline for byte-level structural segmentation."""

from __future__ import annotations

import torch
import torch.nn as nn
from typing import Dict, Tuple

from kethravax.core.taxonomy import ARCHITECTURES, STRUCTURAL_CATEGORIES


class KethraSegBiLSTM(nn.Module):
    """Bidirectional LSTM model for dense byte sequence segmentation (Remigio et al. inspired).
    
    Architecture:
        - Byte Embedding: 256 byte values -> embedding_dim (e.g. 48)
        - BiLSTM: 2 layers, hidden_dim (e.g. 64 per direction = 128 total)
        - Three Output Heads:
          1. cat_head: Linear(128, num_categories) -> frame structural logits
          2. arch_head: Linear(128, num_architectures) -> frame architecture logits
          3. boundary_head: Linear(128, 1) -> boundary transition probability
    """

    def __init__(
        self,
        embedding_dim: int = 48,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_categories: int = len(STRUCTURAL_CATEGORIES),
        num_architectures: int = len(ARCHITECTURES),
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(256, embedding_dim)
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            bidirectional=True,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        total_hidden = hidden_dim * 2
        self.cat_head = nn.Sequential(
            nn.Linear(total_hidden, total_hidden // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(total_hidden // 2, num_categories),
        )
        self.arch_head = nn.Sequential(
            nn.Linear(total_hidden, total_hidden // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(total_hidden // 2, num_architectures),
        )
        self.boundary_head = nn.Sequential(
            nn.Linear(total_hidden, total_hidden // 4),
            nn.ReLU(),
            nn.Linear(total_hidden // 4, 1),
        )

    def forward(
        self, byte_tokens: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass.
        
        Args:
            byte_tokens: (batch_size, sequence_length) of byte integers in [0, 255].
            
        Returns:
            Tuple of (cat_logits, arch_logits, boundary_logits):
                - cat_logits: (batch_size, sequence_length, num_categories)
                - arch_logits: (batch_size, sequence_length, num_architectures)
                - boundary_logits: (batch_size, sequence_length)
        """
        # Embed bytes: (B, L, E)
        embedded = self.embedding(byte_tokens)
        lstm_out, _ = self.lstm(embedded)  # (B, L, 2 * H)

        cat_logits = self.cat_head(lstm_out)
        arch_logits = self.arch_head(lstm_out)
        boundary_logits = self.boundary_head(lstm_out).squeeze(-1)

        return cat_logits, arch_logits, boundary_logits

