"""Adapters for local AI services (opencode agent server)."""

from __future__ import annotations

from .client import OpenCodeClient, OpenCodeError
from .config import OpenCodeConfig, get_opencode_config

__all__ = ["OpenCodeClient", "OpenCodeConfig", "OpenCodeError", "get_opencode_config"]
