"""
Patient Storage & Artifact Synchronization Service for SleepLens.
Organizes all patient inputs, raw archives, extracted brain signals,
AI stage predictions, metrics, and clinical reports into dedicated patient directories.
Adheres to backend_coding_guidelines/01_PROJECT_STRUCTURE.md.
"""

import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List

from django.conf import settings
from apps.patients.models.patient import Patient
from apps.studies.models.study import SleepStudy
from apps.hypnograms.models.epoch import SleepEpoch
from apps.metrics.models.study_metric import StudyMetricsSummary
from apps.reports.models.report import ClinicalReport

logger = logging.getLogger("SleepLensPatientStorage")

STAGE_NAMES = {
    0: "Wake",
    1: "N1 (Light Sleep)",
    2: "N2 (Backbone Sleep)",
    3: "N3 (Deep Slow-Wave Sleep)",
    4: "REM (Dream Sleep)",
    -1: "Unscored"
}

class PatientStorageService:
    """Manages dedicated patient folder structures and artifact synchronization."""

    @classmethod
    def get_patient_directory(cls, patient: Patient) -> Path:
        """Returns the dedicated root folder for a patient."""
        safe_mrn = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in patient.mrn)
        patient_dir = Path(settings.MEDIA_ROOT) / "patients" / safe_mrn
        patient_dir.mkdir(parents=True, exist_ok=True)
        return patient_dir

    @classmethod
    def get_study_directory(cls, study: SleepStudy) -> Path:
        """Returns the specific study directory inside the patient folder."""
        patient_dir = cls.get_patient_directory(study.patient)
        study_dir = patient_dir / f"study_{study.id}"
        study_dir.mkdir(parents=True, exist_ok=True)
        return study_dir

    @classmethod
    def export_study_artifacts(cls, study: SleepStudy):
        """
        Synchronizes all study artifacts into the dedicated patient folder:
        - patient_profile.json (demographics & medical history)
        - staging/hypnogram_staging.json (all epoch stage predictions & micro-metrics)
        - staging/stage_distribution.json (percentages & counts)
        - metrics/sqi_metrics.json (all 7 categories & SQI composite score)
        - metrics/category_summaries.json (category status)
        - reports/clinical_report.md & clinical_report.json (full diagnostic report)
        """
        study_dir = cls.get_study_directory(study)
        patient = study.patient

        # 1. Patient Profile
        age = (datetime.date.today().year - patient.birth_date.year) if patient.birth_date else "N/A"
        profile_data = {
            "patient_id": str(patient.id),
            "mrn": patient.mrn,
            "full_name": f"{patient.first_name} {patient.last_name}",
            "age": age,
            "biological_sex": patient.biological_sex,
            "medical_history": patient.medical_history,
            "study_type": study.study_type,
            "study_date": str(study.study_date),
            "total_epochs": study.total_epochs,
            "duration_minutes": study.duration_minutes,
            "status": study.status,
            "folder_path": str(study_dir)
        }
        with open(study_dir / "patient_profile.json", "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)

        # 2. Staging Artifacts (AI stage predictions + brainwave micro-metrics)
        staging_dir = study_dir / "staging"
        staging_dir.mkdir(exist_ok=True)

        epochs = SleepEpoch.objects.filter(study=study).order_by("epoch_index")
        epochs_data = []
        stage_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, -1: 0}

        for ep in epochs:
            stage_counts[ep.stage] = stage_counts.get(ep.stage, 0) + 1
            epochs_data.append({
                "epoch_index": ep.epoch_index,
                "start_seconds": ep.start_seconds,
                "stage": ep.stage,
                "stage_name": STAGE_NAMES.get(ep.stage, "Unknown"),
                "ai_predicted_stage": ep.ai_predicted_stage,
                "confidence": ep.confidence,
                "is_manually_corrected": ep.is_manually_corrected,
                "correction_reason": ep.correction_reason,
                "spectral_and_micro_metrics": ep.metrics or {}
            })

        with open(staging_dir / "hypnogram_staging.json", "w", encoding="utf-8") as f:
            json.dump(epochs_data, f, indent=2, ensure_ascii=False)

        total_scored = sum(v for k, v in stage_counts.items() if k != -1) or 1
        distribution = {
            "total_epochs": len(epochs),
            "wake": {"count": stage_counts[0], "percentage": round((stage_counts[0] / total_scored) * 100, 2)},
            "n1": {"count": stage_counts[1], "percentage": round((stage_counts[1] / total_scored) * 100, 2)},
            "n2": {"count": stage_counts[2], "percentage": round((stage_counts[2] / total_scored) * 100, 2)},
            "n3": {"count": stage_counts[3], "percentage": round((stage_counts[3] / total_scored) * 100, 2)},
            "rem": {"count": stage_counts[4], "percentage": round((stage_counts[4] / total_scored) * 100, 2)},
        }
        with open(staging_dir / "stage_distribution.json", "w", encoding="utf-8") as f:
            json.dump(distribution, f, indent=2, ensure_ascii=False)

        # 3. Metrics Artifacts
        metrics_dir = study_dir / "metrics"
        metrics_dir.mkdir(exist_ok=True)

        summary = getattr(study, "metrics_summary", None)
        if summary:
            metrics_payload = {
                "sqi_score": summary.sqi_score,
                "sqi_category": summary.sqi_category,
                "is_manually_adjusted": summary.is_manually_adjusted,
                "clinical_alerts": summary.clinical_alerts,
                "metrics_data": summary.metrics_data,
                "ai_raw_metrics": summary.ai_raw_metrics,
                "computed_at": str(summary.computed_at)
            }
            with open(metrics_dir / "sqi_metrics.json", "w", encoding="utf-8") as f:
                json.dump(metrics_payload, f, indent=2, ensure_ascii=False)

            with open(metrics_dir / "category_summaries.json", "w", encoding="utf-8") as f:
                json.dump(summary.category_summaries or {}, f, indent=2, ensure_ascii=False)

        # 4. Reports Artifacts
        reports_dir = study_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

        report = ClinicalReport.objects.filter(study=study).first()
        if report:
            report_dict = {
                "llm_model_name": report.llm_model_name,
                "executive_summary": report.executive_summary,
                "architecture_findings": report.architecture_findings,
                "respiratory_and_micro_notes": report.respiratory_and_micro_notes,
                "differential_diagnoses": report.differential_diagnoses,
                "clinical_recommendations": report.clinical_recommendations,
                "physician_notes": report.physician_notes,
                "is_signed_off": report.is_signed_off,
                "signed_off_at": str(report.signed_off_at) if report.signed_off_at else None,
                "updated_at": str(report.updated_at)
            }
            with open(reports_dir / "clinical_report.json", "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)

            if report.raw_markdown:
                with open(reports_dir / "clinical_report.md", "w", encoding="utf-8") as f:
                    f.write(report.raw_markdown)

        logger.info(f"Synchronized all patient artifacts to {study_dir}")

    @classmethod
    def get_patient_context_for_llm(cls, study: SleepStudy) -> str:
        """
        Builds a comprehensive, grounded prompt header for OpenCode giving it
        exact filesystem paths to the patient's data, signals, and metric files.
        """
        study_dir = cls.get_study_directory(study)
        patient = study.patient
        summary = getattr(study, "metrics_summary", None)
        metrics = summary.metrics_data if summary else {}
        age = (datetime.date.today().year - patient.birth_date.year) if patient.birth_date else "N/A"

        return (
            f"=== PATIENT RECORD & POLYSOMNOGRAPHY REPOSITORY ===\n"
            f"Patient: {patient.first_name} {patient.last_name} (MRN: {patient.mrn})\n"
            f"Demographics: Age {age}, Sex {patient.biological_sex}\n"
            f"Dedicated Patient Data Directory on disk:\n"
            f"  {study_dir}\n\n"
            f"Files Available in this Patient's Directory:\n"
            f"  1. extracted/epochs/ (Epoch-by-epoch signals: EEG Fpz-Cz, EEG Pz-Oz, EOG, EMG, Nasal Flow)\n"
            f"  2. staging/hypnogram_staging.json (AI model 5-class sleep stage predictions & confidence)\n"
            f"  3. staging/stage_distribution.json (Stage breakdown percentages: Wake, N1, N2, N3, REM)\n"
            f"  4. metrics/sqi_metrics.json (7-category computed metrics & Sleep Quality Index)\n"
            f"  5. reports/clinical_report.md (Generated clinical diagnostic report)\n\n"
            f"Active Polysomnography Summary:\n"
            f"  • SQI Score: {summary.sqi_score if summary else 'N/A'}/100 ({summary.sqi_category if summary else 'N/A'})\n"
            f"  • Sleep Efficiency (SE): {metrics.get('se_pct', 'N/A')}%\n"
            f"  • Total Sleep Time (TST): {metrics.get('tst_min', 'N/A')} min\n"
            f"  • Wake After Sleep Onset (WASO): {metrics.get('waso_min', 'N/A')} min\n"
            f"  • Deep Sleep (N3): {metrics.get('n3_pct_tst', 'N/A')}%\n"
            f"  • REM Sleep: {metrics.get('rem_pct_tst', 'N/A')}%\n"
            f"  • Sleep Fragmentation Index (SFI): {metrics.get('sfi', 'N/A')}/hr\n"
            f"  • Apnea Index (AHI): {metrics.get('apnea_index', 'N/A')}/hr\n"
            f"  • Active Clinical Alerts: {', '.join(summary.clinical_alerts) if summary and summary.clinical_alerts else 'None'}\n"
            f"====================================================\n"
        )
