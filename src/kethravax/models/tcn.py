"""Temporal Convolutional Network (TCN) with dilated causal/non-causal residual blocks."""

from __future__ import annotations

import torch
import torch.nn as nn
from typing import List, Tuple

from kethravax.core.taxonomy import ARCHITECTURES, STRUCTURAL_CATEGORIES


class DilatedResidualBlock(nn.Module):
    """Residual 1D convolutional block with dilation and weight normalization."""

    def __init__(
        self,
        channels: int,
        kernel_size: int = 5,
        dilation: int = 1,
        dropout: float = 0.15,
    ) -> None:
        super().__init__()
        padding = (kernel_size - 1) * dilation // 2
        self.conv1 = nn.Conv1d(
            channels,
            channels,
            kernel_size=kernel_size,
            padding=padding,
            dilation=dilation,
        )
        self.bn1 = nn.BatchNorm1d(channels)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.conv2 = nn.Conv1d(
            channels,
            channels,
            kernel_size=kernel_size,
            padding=padding,
            dilation=dilation,
        )
        self.bn2 = nn.BatchNorm1d(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.conv2(out)
        out = self.bn2(out)
        return self.relu(out + residual)


class KethraSegTCN(nn.Module):
    """Dilated Temporal Convolutional Network for multi-class structural segmentation.
    
    Receptive field expands exponentially with dilation schedule [1, 2, 4, 8, 16],
    allowing the model to observe up to 256 bytes of context without recurrent latency.
    """

    def __init__(
        self,
        embedding_dim: int = 48,
        channels: int = 64,
        dilations: List[int] = [1, 2, 4, 8, 16],
        kernel_size: int = 5,
        num_categories: int = len(STRUCTURAL_CATEGORIES),
        num_architectures: int = len(ARCHITECTURES),
        dropout: float = 0.15,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(256, embedding_dim)
        self.in_proj = nn.Conv1d(embedding_dim, channels, kernel_size=1)

        self.blocks = nn.ModuleList([
            DilatedResidualBlock(
                channels=channels,
                kernel_size=kernel_size,
                dilation=d,
                dropout=dropout,
            )
            for d in dilations
        ])

        self.cat_head = nn.Sequential(
            nn.Conv1d(channels, channels // 2, kernel_size=1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Conv1d(channels // 2, num_categories, kernel_size=1),
        )
        self.arch_head = nn.Sequential(
            nn.Conv1d(channels, channels // 2, kernel_size=1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Conv1d(channels // 2, num_architectures, kernel_size=1),
        )
        self.boundary_head = nn.Sequential(
            nn.Conv1d(channels, channels // 4, kernel_size=1),
            nn.ReLU(),
            nn.Conv1d(channels // 4, 1, kernel_size=1),
        )

    def forward(
        self, byte_tokens: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass.
        
        Args:
            byte_tokens: (batch_size, sequence_length)
            
        Returns:
            Tuple of (cat_logits, arch_logits, boundary_logits):
                - cat_logits: (batch_size, sequence_length, num_categories)
                - arch_logits: (batch_size, sequence_length, num_architectures)
                - boundary_logits: (batch_size, sequence_length)
        """
        # Embed: (B, L, E) -> Transpose to (B, E, L) for Conv1d
        x = self.embedding(byte_tokens).transpose(1, 2)
        x = self.in_proj(x)

        for block in self.blocks:
            x = block(x)

        cat_logits = self.cat_head(x).transpose(1, 2)
        arch_logits = self.arch_head(x).transpose(1, 2)
        boundary_logits = self.boundary_head(x).squeeze(1)

        return cat_logits, arch_logits, boundary_logits

