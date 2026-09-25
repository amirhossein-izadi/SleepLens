"""PyTorch models for the wearable benchmark (adapted from public repos).

Both models are re-implementations of published architectures, adapted to the
Sleep-EDF surrogate input. They are NOT the original code and are labelled as
adapted variants in every report:

  UNet1D
      1D U-Net encoder/decoder with residual convolution blocks, inspired by
      MADSOLSEN/SleepStagePrediction (ResUNet). The original operates on 2D
      accel+PPG spectrograms in TensorFlow; here it is ported to 1D envelopes
      in PyTorch (tensorflow-addons is discontinued).

  WatchSleepNet1D
      ResNet1D feature extractor + TCN + BiLSTM + multi-head attention, ported
      from WillKeWang/WatchSleepNet_public. The original consumes IBI sequences
      (750 samples per 30-s epoch); here the single input channel is a
      motion/EOG envelope. Width/epochs reduced for hackathon compute.
"""

from __future__ import annotations

import torch
from torch import nn


class ResBlock1d(nn.Module):
    """Two-conv residual block with strided downsampling (WatchSleepNet-style)."""

    def __init__(self, in_ch: int, out_ch: int, stride: int = 1, kernel_size: int = 3):
        super().__init__()
        pad = kernel_size // 2
        self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size, stride=stride, padding=pad, bias=False)
        self.bn1 = nn.BatchNorm1d(out_ch)
        self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size, stride=1, padding=pad, bias=False)
        self.bn2 = nn.BatchNorm1d(out_ch)
        self.act = nn.ReLU(inplace=True)
        self.drop = nn.Dropout(0.2)
        self.downsample = nn.Sequential()
        if stride != 1 or in_ch != out_ch:
            self.downsample = nn.Sequential(
                nn.Conv1d(in_ch, out_ch, 1, stride=stride, bias=False),
                nn.BatchNorm1d(out_ch),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = self.downsample(x)
        x = self.drop(self.act(self.bn1(self.conv1(x))))
        x = self.drop(self.act(self.bn2(self.conv2(x))))
        return x + res


class SegmentFeatureExtractor(nn.Module):
    """Maps one 30-s segment (1, L) to a 256-d embedding."""

    def __init__(self, in_channels: int = 1, num_layers: int = 4, out_dim: int = 256):
        super().__init__()
        layers: list[nn.Module] = [nn.Conv1d(in_channels, 16, kernel_size=7, stride=1, padding=3), nn.ReLU(inplace=True)]
        ch = 16
        stride = 1
        for i in range(num_layers):
            out_ch = 32 * (2**i)
            stride = 4
            layers.append(ResBlock1d(ch, out_ch, stride=stride))
            ch = out_ch
        layers.append(nn.Conv1d(ch, out_dim, kernel_size=3, stride=stride))
        layers.append(nn.AdaptiveAvgPool1d(1))
        self.layers = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x).flatten(1)


class TCNBlock(nn.Module):
    """Dilated causal-free TCN stack over the segment axis."""

    def __init__(self, in_ch: int, out_ch: int, kernel_size: int = 3, num_layers: int = 3):
        super().__init__()
        layers = []
        ch = in_ch
        dilation = 1
        for _ in range(num_layers):
            layers.append(
                nn.Sequential(
                    nn.Conv1d(ch, out_ch, kernel_size, padding=(kernel_size - 1) * dilation // 2, dilation=dilation),
                    nn.BatchNorm1d(out_ch),
                    nn.ReLU(inplace=True),
                    nn.Dropout(0.2),
                )
            )
            ch = out_ch
            dilation *= 2
        self.layers = nn.ModuleList(layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for layer in self.layers:
            x = layer(x)
        return x


class BiLSTMAttention(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_heads: int, num_layers: int, use_attention: bool = True):
        super().__init__()
        self.use_attention = use_attention
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, bidirectional=True)
        if use_attention:
            self.attention = nn.MultiheadAttention(hidden_size * 2, num_heads, batch_first=True)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        lengths_cpu = lengths.detach().to("cpu", dtype=torch.int64)
        packed = nn.utils.rnn.pack_padded_sequence(x, lengths_cpu, batch_first=True, enforce_sorted=False)
        out, _ = self.lstm(packed)
        out, _ = nn.utils.rnn.pad_packed_sequence(out, batch_first=True)
        if self.use_attention:
            max_len = out.size(1)
            key_mask = torch.arange(max_len, device=out.device).unsqueeze(0) >= lengths.to(out.device).unsqueeze(1)
            out, _ = self.attention(out, out, out, key_padding_mask=key_mask)
        return out


class WatchSleepNet1D(nn.Module):
    """ResNet1D + TCN + BiLSTM(+attention) sequence-to-sequence classifier."""

    def __init__(
        self,
        num_classes: int = 3,
        num_channels: int = 64,
        kernel_size: int = 3,
        hidden_dim: int = 128,
        num_heads: int = 4,
        num_layers: int = 2,
        tcn_layers: int = 3,
        use_tcn: bool = True,
        use_attention: bool = True,
    ):
        super().__init__()
        self.feature_extractor = SegmentFeatureExtractor(1, 4, 256)
        self.use_tcn = use_tcn
        if use_tcn:
            self.tcn = TCNBlock(256, num_channels, kernel_size, tcn_layers)
            lstm_input = num_channels
        else:
            lstm_input = 256
        self.lstm = BiLSTMAttention(lstm_input, hidden_dim, num_heads, num_layers, use_attention)
        self.classifier = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        batch, n_seg, seg_len = x.shape
        feats = self.feature_extractor(x.reshape(-1, 1, seg_len)).reshape(batch, n_seg, -1)
        if self.use_tcn:
            feats = self.tcn(feats.permute(0, 2, 1)).permute(0, 2, 1)
        out = self.lstm(feats, lengths)
        return self.classifier(out)


class ConvBlock1d(nn.Module):
    """Residual double-conv block for the U-Net (GELU, batch norm)."""

    def __init__(self, in_ch: int, out_ch: int, kernel_size: int = 7, dropout: float = 0.1):
        super().__init__()
        pad = kernel_size // 2
        self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size, padding=pad, bias=False)
        self.bn1 = nn.BatchNorm1d(out_ch)
        self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size, padding=pad, bias=False)
        self.bn2 = nn.BatchNorm1d(out_ch)
        self.act = nn.GELU()
        self.drop = nn.Dropout(dropout)
        self.residual = nn.Identity()
        if in_ch != out_ch:
            self.residual = nn.Sequential(nn.Conv1d(in_ch, out_ch, 1, bias=False), nn.BatchNorm1d(out_ch))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = self.residual(x)
        x = self.drop(self.act(self.bn1(self.conv1(x))))
        x = self.drop(self.act(self.bn2(self.conv2(x))))
        return x + res


class UNet1D(nn.Module):
    """1D U-Net over an epoch waveform; global pooling gives one label per epoch."""

    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = 5,
        base: int = 16,
        depth: int = 3,
        kernel_size: int = 5,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.depth = depth
        self.enc_blocks = nn.ModuleList()
        self.pools = nn.ModuleList()
        ch = in_channels
        widths = [base * (2**i) for i in range(depth)]
        for w in widths:
            self.enc_blocks.append(ConvBlock1d(ch, w, kernel_size, dropout))
            self.pools.append(nn.MaxPool1d(2))
            ch = w
        self.bottleneck = ConvBlock1d(ch, ch * 2, kernel_size, dropout)
        ch = ch * 2
        self.up_blocks = nn.ModuleList()
        self.dec_blocks = nn.ModuleList()
        for w in reversed(widths):
            self.up_blocks.append(nn.ConvTranspose1d(ch, w, kernel_size=2, stride=2))
            self.dec_blocks.append(ConvBlock1d(w * 2, w, kernel_size, dropout))
            ch = w
        self.head = nn.Sequential(
            nn.Conv1d(ch, ch, kernel_size=3, padding=1, bias=False),
            nn.GELU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.classifier = nn.Linear(ch, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skips = []
        for block, pool in zip(self.enc_blocks, self.pools):
            x = block(x)
            skips.append(x)
            x = pool(x)
        x = self.bottleneck(x)
        for up, block, skip in zip(self.up_blocks, self.dec_blocks, reversed(skips)):
            x = up(x)
            if x.shape[-1] != skip.shape[-1]:
                x = nn.functional.interpolate(x, size=skip.shape[-1], mode="nearest")
            x = block(torch.cat([skip, x], dim=1))
        x = self.head(x).flatten(1)
        return self.classifier(x)
