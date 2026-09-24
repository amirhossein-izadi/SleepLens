"""
Clinical Prompt Engineering Service for SleepLens.
Transforms polysomnography data, patient history, and SQI metrics into clinical prompts.
Adheres to backend_coding_guidelines/03_DJANGO_PATTERNS.md
"""

from typing import Dict, Any, List
from apps.studies.models.study import SleepStudy
from lib.contracts.study_dto import ClinicalContextDTO

class PromptBuilder:
    """Builds structured clinical prompts for the OpenCode LLM."""

    @classmethod
    def build_clinical_context(cls, study: SleepStudy) -> ClinicalContextDTO:
        patient = study.patient
        summary = getattr(study, "metrics_summary", None)

        sqi_score = summary.sqi_score if summary else 0.0
        sqi_category = summary.sqi_category if summary else "poor"
        key_metrics = summary.metrics_data if summary else {}
        clinical_alerts = summary.clinical_alerts if summary else []

        # Calculate patient age
        age = 45
        if patient.birth_date:
            import datetime
            today = datetime.date.today()
            age = today.year - patient.birth_date.year - ((today.month, today.day) < (patient.birth_date.month, patient.birth_date.day))
        history_text = patient.medical_history or "None documented"
        try:
            doc_texts = []
            if hasattr(study, "files"):
                for sf in study.files.filter(file_type__in=["pdf_document", "text_document"]):
                    txt = sf.preview_data.get("extracted_text")
                    if txt and not str(txt).startswith("No machine-readable"):
                        doc_texts.append(f"[{sf.file_name}]:\n{txt}")
            if doc_texts:
                history_text += "\n\n[EXTRACTED REPORT TEXT FROM ATTACHED DOCUMENTS]:\n" + "\n\n".join(doc_texts)
        except Exception:
            pass

        return ClinicalContextDTO(
            patient_mrn=patient.mrn,
            patient_name=f"{patient.first_name} {patient.last_name}",
            patient_age=age,
            patient_sex=patient.get_biological_sex_display(),
            medical_history=history_text,
            study_date=str(study.study_date),
            sqi_score=sqi_score,
            sqi_category=sqi_category,
            key_metrics=key_metrics,
            clinical_alerts=clinical_alerts
        )
    @classmethod
    def build_report_prompt(cls, context: ClinicalContextDTO) -> str:
        """Constructs system and clinical user prompt for report generation."""
        alerts_text = "\n".join(f"- {a}" for a in context.clinical_alerts) if context.clinical_alerts else "None flagged"

        return f"""You are an expert board-certified somnologist (sleep medicine physician).
Analyze this nocturnal polysomnography recording and produce a comprehensive clinical report.

PATIENT INFORMATION:
- Name: {context.patient_name} (Age: {context.patient_age}, Sex: {context.patient_sex})
- Medical Record Number (MRN): {context.patient_mrn}
- Study Date: {context.study_date}
- Clinical History & Complaints: {context.medical_history}

POLYSOMNOGRAPHIC & SQI METRICS:
- Sleep Quality Index (SQI): {context.sqi_score:.1f} / 100 ({context.sqi_category.upper()})
- Total Sleep Time (TST): {context.key_metrics.get('tst_min', 'N/A')} minutes
- Sleep Efficiency (SE): {context.key_metrics.get('se_pct', 'N/A')}% (Normal: >= 85%)
- Wake After Sleep Onset (WASO): {context.key_metrics.get('waso_min', 'N/A')} minutes (Normal: <= 30 min)
- Sleep Onset Latency (SOL): {context.key_metrics.get('sol_min', 'N/A')} minutes (Normal: 10 - 20 min)
- REM Latency: {context.key_metrics.get('rem_lat_min', 'N/A')} minutes (Normal: 70 - 120 min)
- Sleep Fragmentation Index (SFI): {context.key_metrics.get('sfi', 'N/A')} events/hr (Normal: <= 15/hr)
- Stage N1: {context.key_metrics.get('n1_pct_tst', 'N/A')}% (Normal: 2 - 5%)
- Stage N2: {context.key_metrics.get('n2_pct_tst', 'N/A')}% (Normal: 45 - 55%)
- Stage N3 (Deep Sleep): {context.key_metrics.get('n3_pct_tst', 'N/A')}% (Normal: 15 - 25%)
- Stage REM (Dream Sleep): {context.key_metrics.get('rem_pct_tst', 'N/A')}% (Normal: 20 - 25%)
- Slow-Wave Activity Sum (SWA): {context.key_metrics.get('swa_sum', 'N/A')} uV^2
- Apnea Index (AHI proxy): {context.key_metrics.get('apnea_index', 'N/A')} events/hr (Normal: < 5/hr)
- REM Atonia Ratio: {context.key_metrics.get('rem_atonia_ratio', 'N/A')} (Normal: > 1.3)

FLAGGED CLINICAL ALERTS:
{alerts_text}

INSTRUCTIONS:
Provide a structured diagnostic report with:
1. Executive Summary: Concise overview of the study and headline findings.
2. Architecture Findings: Interpretation of sleep stages, deep N3 restoration, and sleep efficiency.
3. Respiratory & Microstructure Notes: Interpretation of breathing pauses, sleep spindles, and awakenings.
4. Differential Diagnoses: 2-3 potential diagnoses with ICD-10 codes where appropriate.
5. Actionable Clinical Recommendations: Clear therapeutic next steps for the physician (e.g. CBT-I, positional therapy, CPAP titration)."""
