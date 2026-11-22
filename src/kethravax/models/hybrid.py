"""KethraSeg Hybrid Model: Multiscale 1D Convolutions + Recurrent Backbone + Dual Boundary Head."""

from __future__ import annotations

import torch
import torch.nn as nn
from typing import Tuple

from kethravax.core.taxonomy import ARCHITECTURES, STRUCTURAL_CATEGORIES


class MultiscaleFeatureExtractor(nn.Module):
    """Parallel 1D convolutions with diverse kernel widths (3, 5, 9, 17).
    
    Captures:
        - 3-byte: short instruction opcodes, prefixes (e.g. REX, ModR/M).
        - 5-byte: average instruction lengths, 32-bit immediate operands.
        - 9-byte: 64-bit immediate pointers, double-word alignment, short prologues.
        - 17-byte: basic block entry points, string runs, alignment fills.
    """

    def __init__(self, in_channels: int, out_channels_per_branch: int = 16) -> None:
        super().__init__()
        self.conv3 = nn.Conv1d(in_channels, out_channels_per_branch, kernel_size=3, padding=1)
        self.conv5 = nn.Conv1d(in_channels, out_channels_per_branch, kernel_size=5, padding=2)
        self.conv9 = nn.Conv1d(in_channels, out_channels_per_branch, kernel_size=9, padding=4)
        self.conv17 = nn.Conv1d(in_channels, out_channels_per_branch, kernel_size=17, padding=8)
        self.bn = nn.BatchNorm1d(out_channels_per_branch * 4)
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        c3 = self.conv3(x)
        c5 = self.conv5(x)
        c9 = self.conv9(x)
        c17 = self.conv17(x)
        out = torch.cat([c3, c5, c9, c17], dim=1)
        return self.relu(self.bn(out))


class KethraSegHybrid(nn.Module):
    """The flagship KethraSeg Hybrid Architecture.
    
    Combines:
    1. Byte Embedding (256 -> 48)
    2. Multiscale 1D Feature Extractor (4 branches = 64 channels)
    3. Bidirectional Recurrent Backbone (BiGRU, hidden_dim=48, 1 layer)
    4. Dual Classification & Boundary Heads with uncertainty calibration.
    """

    def __init__(
        self,
        embedding_dim: int = 48,
        conv_branch_channels: int = 16,
        rnn_hidden_dim: int = 48,
        num_categories: int = len(STRUCTURAL_CATEGORIES),
        num_architectures: int = len(ARCHITECTURES),
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(256, embedding_dim)
        self.multiscale = MultiscaleFeatureExtractor(
            in_channels=embedding_dim,
            out_channels_per_branch=conv_branch_channels,
        )
        total_conv_dim = conv_branch_channels * 4

        # Recurrent backbone across temporal steps
        self.rnn = nn.GRU(
            input_size=total_conv_dim,
            hidden_size=rnn_hidden_dim,
            num_layers=1,
            bidirectional=True,
            batch_first=True,
        )
        fusion_dim = total_conv_dim + (rnn_hidden_dim * 2)

        self.dropout = nn.Dropout(dropout)
        self.cat_head = nn.Sequential(
            nn.Linear(fusion_dim, fusion_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim // 2, num_categories),
        )
        self.arch_head = nn.Sequential(
            nn.Linear(fusion_dim, fusion_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim // 2, num_architectures),
        )
        self.boundary_head = nn.Sequential(
            nn.Linear(fusion_dim, fusion_dim // 4),
            nn.ReLU(),
            nn.Linear(fusion_dim // 4, 1),
        )

    def forward(
        self, byte_tokens: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass.
        
        Args:
            byte_tokens: (batch_size, sequence_length)
            
        Returns:
            Tuple of (cat_logits, arch_logits, boundary_logits)
        """
        # Embed: (B, L, E) -> Transpose to (B, E, L) for Conv1d
        embedded = self.embedding(byte_tokens)
        conv_in = embedded.transpose(1, 2)
        conv_out = self.multiscale(conv_in).transpose(1, 2)  # (B, L, total_conv_dim)

        rnn_out, _ = self.rnn(conv_out)  # (B, L, 2 * rnn_hidden)

        # Fuse convolutional and recurrent representations
        fused = torch.cat([conv_out, rnn_out], dim=-1)
        fused = self.dropout(fused)

        cat_logits = self.cat_head(fused)
        arch_logits = self.arch_head(fused)
        boundary_logits = self.boundary_head(fused).squeeze(-1)

        return cat_logits, arch_logits, boundary_logits

