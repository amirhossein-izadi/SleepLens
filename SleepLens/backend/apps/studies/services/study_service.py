"""Study lifecycle service — creation, ownership, reprocessing, PSQI."""

from __future__ import annotations

from typing import Any

import structlog
from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from apps.analysis.tasks import process_study
from apps.studies.models import PSQI, Study
from apps.studies.services.upload_validation import validate_study_upload

logger = structlog.get_logger(__name__)


class StudyService:
    """Explicit study operations used by the API layer."""

    @staticmethod
    def create_study(
        *,
        user: Any,
        uploaded_file: Any,
        patient: Any = None,
        psqi: dict | None = None,
    ) -> Study:
        """Validate, persist (with optional patient and PSQI) and enqueue."""
        validate_study_upload(uploaded_file)
        with transaction.atomic():
            study = Study.objects.create(
                user=user,
                patient=patient,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=int(uploaded_file.size or 0),
            )
            if psqi:
                PSQI.objects.create(study=study, **psqi)
        logger.info(
            "study_uploaded",
            study_id=str(study.id),
            user_id=str(user.id),
            has_patient=patient is not None,
            has_psqi=bool(psqi),
        )
        process_study.delay(str(study.id))
        return study

    @staticmethod
    def get_user_study(*, user: Any, study_id: Any) -> Study:
        """Return the user's study or raise ``NotFound``."""
        study = Study.objects.filter(id=study_id, user=user).first()
        if study is None:
            raise NotFound("Study not found.")
        return study

    @staticmethod
    def set_psqi(*, user: Any, study_id: Any, components: dict[str, int]) -> PSQI:
        """Attach or replace the PSQI questionnaire (all-or-nothing)."""
        study = StudyService.get_user_study(user=user, study_id=study_id)
        with transaction.atomic():
            psqi, _ = PSQI.objects.update_or_create(study=study, defaults=components)
        logger.info("psqi_saved", study_id=str(study.id), global_score=psqi.global_score)
        return psqi

    @staticmethod
    def reprocess(*, user: Any, study_id: Any) -> Study:
        """Reset a study and enqueue processing again."""
        study = StudyService.get_user_study(user=user, study_id=study_id)
        if study.status == "processing":
            raise ValidationError({"study": "Study is already being processed."})
        with transaction.atomic():
            study.status = "uploaded"
            study.status_message = "Queued for processing."
            study.error_message = ""
            study.save(update_fields=["status", "status_message", "error_message", "updated_at"])
        logger.info("study_reprocess_queued", study_id=str(study.id), user_id=str(user.id))
        process_study.delay(str(study.id))
        return study
