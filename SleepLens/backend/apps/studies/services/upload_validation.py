"""Upload validation for study files (EDF only, size capped)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.conf import settings
from rest_framework.exceptions import ValidationError


def validate_study_upload(uploaded_file: Any) -> None:
    """Raise ``ValidationError`` when the upload cannot be a PSG recording."""
    name = getattr(uploaded_file, "name", "") or ""
    extension = Path(name).suffix.lower().lstrip(".")
    if extension not in settings.ALLOWED_STUDY_EXTENSIONS:
        raise ValidationError(
            {
                "file": (
                    f"Unsupported file type '.{extension}'. "
                    f"Allowed: {', '.join(sorted(settings.ALLOWED_STUDY_EXTENSIONS))}."
                )
            }
        )
    size = int(getattr(uploaded_file, "size", 0) or 0)
    if size == 0:
        raise ValidationError({"file": "The uploaded file is empty."})
    if size > settings.MAX_UPLOAD_SIZE:
        limit_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
        raise ValidationError({"file": f"File larger than the {limit_mb} MB limit."})
