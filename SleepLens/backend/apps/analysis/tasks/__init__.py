"""Celery tasks for the analysis app."""

from __future__ import annotations

from .process_study import process_study

__all__ = ["process_study"]
