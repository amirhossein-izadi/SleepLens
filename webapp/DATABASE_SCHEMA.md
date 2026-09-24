# SleepLens — Database Architecture & Schema Specification

This document details the complete database schema design for **SleepLens**, engineered to meet the requirements of sleep medicine specialists while adhering to the guidelines in `backend_coding_guidelines/`.

---

## 1. Architectural Principles

1. **PostgreSQL 16+ with Hybrid Relational + JSONB Model**:
   - High-cardinality, strictly queried clinical entities (patients, studies, reports, epochs, files) use relational tables with strict foreign keys and constraints.
   - **Dynamic Metrics Engine**: Because the exact list, count, and clinical weighting of metrics from `SQI_METRICS.md` will evolve during development, all computed metrics are stored in a schema-less, highly indexed **JSONB** architecture paired with a **Metric Definition Catalog**. Adding, removing, or adjusting 10 or 50 metrics requires **zero database migrations**.
2. **Physician Verification & Human-in-the-Loop Overrides**:
   - **Per-File & Per-Epoch Visibility**: Every file in the uploaded ZIP (raw recordings, individual 30s epoch reports, annotations, metadata) is indexed into a dedicated `StudyFile` record with metadata, previews, and download capabilities.
   - **Stage Correction Audit Trail**: Physicians can view individual epoch files and override AI-predicted sleep stages (`ai_predicted_stage` vs. `stage`).
   - **Metric Overrides & Recalculation**: If the physician identifies an inaccurate metric (e.g., falsely elevated WASO, missed apneas), they can manually adjust the value with a documented clinical rationale. An on-demand recalculation engine updates dependent metrics and the composite SQI score.
3. **UUIDv7 Primary Keys**:
   - Time-ordered, monotonic UUIDs providing sorting by creation time and preventing ID enumeration.
4. **Audit Trail & Timestamps**:
   - Every entity tracks `created_at` and `updated_at`.
5. **No Celery Dependency (Lightweight Task Architecture)**:
   - Study processing states are managed directly via a robust state machine stored on `studies_sleepstudy.status`, executed via Python's built-in `concurrent.futures.ThreadPoolExecutor` inside the Django runtime.

---

## 2. Entity-Relationship Overview

```mermaid
erDiagram
    PATIENT ||--o{ SLEEP_STUDY : "has"
    USER ||--o{ SLEEP_STUDY : "supervises"
    SLEEP_STUDY ||--o{ STUDY_FILE : "contains extracted"
    SLEEP_STUDY ||--o{ SLEEP_EPOCH : "consists of"
    STUDY_FILE ||--o| SLEEP_EPOCH : "backs (optional)"
    SLEEP_STUDY ||--o| STUDY_METRICS_SUMMARY : "produces"
    STUDY_METRICS_SUMMARY ||--o{ METRIC_OVERRIDE : "tracks adjustments"
    SLEEP_STUDY ||--o| CLINICAL_REPORT : "summarized by"
    SLEEP_STUDY ||--o{ CHAT_SESSION : "interrogated via"
    CHAT_SESSION ||--o{ CHAT_MESSAGE : "contains"
    METRIC_DEFINITION }o--o{ STUDY_METRICS_SUMMARY : "describes metadata for"

    STUDY_FILE {
        uuid id PK
        uuid study_id FK
        string file_name
        string relative_path
        string file_type "EPOCH_REPORT | RAW_EDF | ANNOTATION | METADATA"
        bigint file_size_bytes
        int epoch_index "Optional link to 30s epoch"
        jsonb preview_data
        timestamp created_at
    }

    PATIENT {
        uuid id PK
        string mrn UK "Medical Record Number"
        string first_name
        string last_name
        date birth_date
        string biological_sex
        text medical_history
        timestamp created_at
    }

    SLEEP_STUDY {
        uuid id PK
        uuid patient_id FK
        uuid physician_id FK
        date study_date
        string study_type "CASSETTE | TELEMETRY | FULL_PSG"
        string status "UPLOADED | STAGING | METRICS | COMPLETED | FAILED"
        string raw_archive_path
        int total_epochs
        float duration_minutes
        jsonb metadata
        text error_log
    }

    SLEEP_EPOCH {
        uuid id PK
        uuid study_id FK
        uuid file_id FK "Optional link to raw epoch file"
        int epoch_index "0 to N"
        float start_seconds
        int stage "Active clinical stage"
        int ai_predicted_stage "Immutable AI prediction"
        float confidence
        boolean is_manually_corrected
        uuid corrected_by_id FK
        timestamp corrected_at
        string correction_reason
        boolean is_lights_off
    }

    STUDY_METRICS_SUMMARY {
        uuid id PK
        uuid study_id FK "1-to-1"
        float sqi_score "0 to 100"
        string sqi_category "OPTIMAL | GOOD | FAIR | POOR"
        jsonb metrics_data GIN "Current active metrics"
        jsonb ai_raw_metrics "Original algorithmic baseline"
        jsonb overrides "Dictionary of physician adjustments"
        boolean is_manually_adjusted
        timestamp computed_at
    }

    METRIC_OVERRIDE {
        uuid id PK
        uuid study_id FK
        string metric_key
        float original_value
        float adjusted_value
        uuid physician_id FK
        text clinical_rationale
        timestamp created_at
    }

    METRIC_DEFINITION {
        string key PK "e.g. waso_min, se_pct"
        string display_name "Wake After Sleep Onset"
        string category "CONTINUITY | FRAGMENTATION | ARCHITECTURE | ..."
        string unit "minutes | percent | events/hr"
        float normal_min
        float normal_max
        boolean is_active
        boolean show_in_report
    }

    CLINICAL_REPORT {
        uuid id PK
        uuid study_id FK "1-to-1"
        string llm_model_name
        text executive_summary
        text architecture_findings
        text respiratory_findings
        jsonb clinical_recommendations
        text physician_notes
        boolean is_signed_off
        timestamp signed_off_at
    }

    CHAT_SESSION {
        uuid id PK
        uuid study_id FK
        uuid physician_id FK
        string opencode_session_id
        string title
        timestamp created_at
    }

    CHAT_MESSAGE {
        uuid id PK
        uuid session_id FK
        string sender "PHYSICIAN | ASSISTANT | SYSTEM"
        text content
        timestamp created_at
    }
```

---

## 3. Dynamic Metrics & Human-in-the-Loop Architecture

### 3.1 Handling Uncertain & Dynamic Metric Counts
- **No Hardcoded SQL Columns**: The exact count of metrics from `SQI_METRICS.md` can range from 15 to 60+ without touching database migrations.
- **JSONB + GIN Index**: All active values live in `StudyMetricsSummary.metrics_data`.
- **MetricDefinition Catalog**: Defines human-readable names, units, and normal ranges.

### 3.2 Physician File Inspection & Manual Overrides
1. **File Transparency**: When a ZIP of 30-second epoch reports is uploaded, each individual file is registered in `StudyFile`. The doctor can inspect file contents, view signal previews, or download raw files.
2. **Epoch Stage Editing**:
   - An epoch retains `ai_predicted_stage` (original) and `stage` (effective).
   - If the doctor changes an epoch from `N1` to `N2`, `is_manually_corrected` becomes `True`, and an audit timestamp + physician ID are recorded.
3. **Metric Overrides**:
   - If the doctor detects an inaccurate metric (e.g. noise-induced arousal index or missed wake time), they can update the value directly.
   - The original value is preserved in `ai_raw_metrics`, while `metrics_data` reflects the doctor's override.
   - A row is written to `MetricOverride` for legal/clinical compliance.
4. **On-Demand Recalculation**:
   - Endpoint: `POST /api/v1/studies/{id}/metrics/recalculate/`
   - Recalculates dependent metrics (e.g., Sleep Efficiency, WASO, SFI, and the final SQI score) based on edited epoch stages.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              HUMAN-IN-THE-LOOP FLOW                                    │
│                                                                                        │
│  [1. Upload ZIP] ──▶ Extracted files registered in `StudyFile` (Available to Doctor)   │
│                             │                                                          │
│                             ▼                                                          │
│  [2. AI Staging] ──▶ `SleepEpoch.ai_predicted_stage` populated                         │
│                             │                                                          │
│                             ▼                                                          │
│  [3. Doctor Review]                                                                    │
│         ├── Inspects Epoch File & Signal Preview (via `StudyFile`)                     │
│         ├── Corrects Stage (e.g., Epoch #142: Wake ➔ N1)                               │
│         └── Adjusts Inaccurate Metric (e.g., `waso_min`: 85 min ➔ 60 min)             │
│                             │                                                          │
│                             ▼                                                          │
│  [4. Recalculation Engine]                                                             │
│         ├── Updates `StudyMetricsSummary.metrics_data` & `overrides`                   │
│         ├── Re-evaluates SQI score (e.g., 68 ➔ 74)                                     │
│         └── Logs audit trail in `MetricOverride`                                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Detailed Table Specifications & Django Models

### 4.1 `apps.studies.models.study_file`
Tracks every file extracted from the patient's ZIP archive.

```python
import uuid
from django.db import models

class StudyFileType(models.TextChoices):
    EPOCH_REPORT = "epoch_report", "30-Second Epoch Report"
    RAW_EDF = "raw_edf", "Raw Polysomnography (.edf / .epf)"
    ANNOTATION_EDF = "annotation_edf", "Hypnogram / Annotation (.edf)"
    METADATA_EXCEL = "metadata_excel", "Demographics / Protocol (.xls / .xlsx)"
    NUMPY_ARRAY = "numpy_array", "Preprocessed Epoch Array (.npz)"
    OTHER = "other", "Other Attachment"

class StudyFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    study = models.ForeignKey("studies.SleepStudy", on_delete=models.CASCADE, related_name="files")
    
    file_name = models.CharField(max_length=255)
    relative_path = models.CharField(max_length=512, help_text="Path relative to study extraction directory")
    file_type = models.CharField(max_length=30, choices=StudyFileType.choices, default=StudyFileType.OTHER, db_index=True)
    file_size_bytes = models.BigIntegerField(default=0)
    file_hash_sha256 = models.CharField(max_length=64, blank=True, default="")
    
    # Optional direct link to an epoch index (if this file represents a 30s epoch report)
    epoch_index = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    
    # Parsed preview for quick UI rendering (e.g. channel names, sampling rate, epoch summary)
    preview_data = models.JSONBField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "studies_studyfile"
        ordering = ("epoch_index", "file_name")
        indexes = [
            models.Index(fields=["study", "file_type"]),
            models.Index(fields=["study", "epoch_index"]),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.file_type}) - Study {self.study_id}"
```

---

### 4.2 `apps.patients.models.patient`
Stores patient demographics and clinical history.

```python
import uuid
from django.db import models

class BiologicalSex(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other / Not Disclosed"

class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    mrn = models.CharField(max_length=64, unique=True, db_index=True, help_text="Medical Record Number")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    biological_sex = models.CharField(max_length=10, choices=BiologicalSex.choices, default=BiologicalSex.OTHER)
    medical_history = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patients_patient"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mrn})"
```

---

### 4.3 `apps.studies.models.study`
Tracks uploaded sessions and coordinates the processing state machine.

```python
import uuid
from django.db import models
from django.conf import settings

class StudyStatus(models.TextChoices):
    UPLOADED = "uploaded", "Uploaded (Pending)"
    EXTRACTING = "extracting", "Extracting Archive"
    STAGING = "staging", "Predicting 30s Sleep Stages"
    COMPUTING_METRICS = "computing_metrics", "Extracting SQI & Metrics"
    GENERATING_REPORT = "generating_report", "Generating AI Clinical Report"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Processing Failed"

class StudyType(models.TextChoices):
    CASSETTE_HOME = "cassette_home", "Sleep-Cassette (Home Study)"
    TELEMETRY_HOSPITAL = "telemetry_hospital", "Sleep-Telemetry (Hospital Study)"
    FULL_PSG = "full_psg", "Full In-Lab Polysomnography"

class SleepStudy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="studies")
    physician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="supervised_studies")
    
    study_date = models.DateField(help_text="Date recording began")
    study_type = models.CharField(max_length=30, choices=StudyType.choices, default=StudyType.FULL_PSG)
    status = models.CharField(max_length=30, choices=StudyStatus.choices, default=StudyStatus.UPLOADED, db_index=True)
    
    raw_archive = models.FileField(upload_to="studies/raw_zips/%Y/%m/")
    extracted_path = models.CharField(max_length=512, blank=True, default="")
    
    total_epochs = models.PositiveIntegerField(default=0)
    duration_minutes = models.FloatField(default=0.0)
    
    metadata = models.JSONBField(default=dict, blank=True)
    error_log = models.TextField(blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "studies_sleepstudy"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["patient", "-study_date"]),
            models.Index(fields=["status", "-created_at"]),
        ]
```

---

### 4.4 `apps.hypnograms.models.epoch`
Stores 30s epoch staging results, supports physician manual stage correction, and links to raw epoch files.

```python
import uuid
from django.db import models
from django.conf import settings

class SleepStage(models.IntegerChoices):
    UNSCORED = -1, "Unscored / Artifact"
    WAKE = 0, "Wake"
    N1 = 1, "N1 (Light Sleep)"
    N2 = 2, "N2 (Core Sleep)"
    N3 = 3, "N3 (Deep / Slow Wave Sleep)"
    REM = 4, "REM (Dream Sleep)"

class SleepEpoch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    study = models.ForeignKey("studies.SleepStudy", on_delete=models.CASCADE, related_name="epochs")
    file = models.ForeignKey("studies.StudyFile", on_delete=models.SET_NULL, null=True, blank=True, related_name="epochs", help_text="Underlying epoch file if provided")
    
    epoch_index = models.PositiveIntegerField(help_text="0-indexed 30-second block order")
    start_seconds = models.FloatField(help_text="Offset from recording start in seconds")
    
    # Active clinical stage (editable by physician)
    stage = models.SmallIntegerField(choices=SleepStage.choices, default=SleepStage.UNSCORED)
    
    # Immutable baseline AI prediction
    ai_predicted_stage = models.SmallIntegerField(choices=SleepStage.choices, default=SleepStage.UNSCORED)
    confidence = models.FloatField(default=1.0, help_text="AI staging confidence score [0.0 - 1.0]")
    
    # Physician correction tracking
    is_manually_corrected = models.BooleanField(default=False, db_index=True)
    corrected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="epoch_corrections")
    corrected_at = models.DateTimeField(null=True, blank=True)
    correction_reason = models.CharField(max_length=255, blank=True, default="")
    
    is_lights_off = models.BooleanField(default=True)
    
    class Meta:
        db_table = "hypnograms_sleepepoch"
        ordering = ("study", "epoch_index")
        constraints = [
            models.UniqueConstraint(fields=["study", "epoch_index"], name="unique_study_epoch_index")
        ]
        indexes = [
            models.Index(fields=["study", "epoch_index"]),
            models.Index(fields=["study", "stage"]),
            models.Index(fields=["study", "is_manually_corrected"]),
        ]
```

---

### 4.5 `apps.metrics.models.study_metric` & `apps.metrics.models.metric_override`
Stores dynamic metrics, preserves the original AI baseline, and tracks physician metric overrides.

```python
import uuid
from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex

class SQICategory(models.TextChoices):
    OPTIMAL = "optimal", "Optimal (> 85)"
    GOOD = "good", "Good (75 - 84)"
    FAIR = "fair", "Fair (60 - 74)"
    POOR = "poor", "Poor (< 60)"

class StudyMetricsSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    study = models.OneToOneField("studies.SleepStudy", on_delete=models.CASCADE, related_name="metrics_summary")
    
    sqi_score = models.FloatField(db_index=True, help_text="Unified Sleep Quality Index score [0 - 100]")
    sqi_category = models.CharField(max_length=20, choices=SQICategory.choices, db_index=True)
    
    # Active metrics currently in effect (incorporates doctor manual adjustments)
    metrics_data = models.JSONBField(default=dict)
    
    # Original AI-calculated metrics (untouched baseline)
    ai_raw_metrics = models.JSONBField(default=dict)
    
    # Grouped summary scores for UI categories
    category_summaries = models.JSONBField(default=dict)
    
    # Audit dictionary of active overrides: {"waso_min": {"original": 85, "override": 60, "reason": "...", ...}}
    overrides = models.JSONBField(default=dict, blank=True)
    is_manually_adjusted = models.BooleanField(default=False, db_index=True)
    
    clinical_alerts = models.JSONBField(default=list, blank=True)
    computed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "metrics_studymetricssummary"
        indexes = [
            models.Index(fields=["sqi_category", "-sqi_score"]),
            GinIndex(fields=["metrics_data"], name="metrics_data_gin_idx"),
        ]


class MetricOverride(models.Model):
    """
    Permanent audit log of every manual metric adjustment made by a physician.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    study = models.ForeignKey("studies.SleepStudy", on_delete=models.CASCADE, related_name="metric_overrides")
    physician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="metric_overrides")
    
    metric_key = models.CharField(max_length=64, db_index=True)
    original_value = models.FloatField()
    adjusted_value = models.FloatField()
    clinical_rationale = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "metrics_metricoverride"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["study", "metric_key"]),
        ]
```

---

### 4.6 `apps.metrics.models.metric_definition`
Metadata catalog for dynamic metric presentation and clinical reference ranges.

```python
from django.db import models

class MetricCategory(models.TextChoices):
    CONTINUITY = "continuity", "Continuity"
    FRAGMENTATION = "fragmentation", "Fragmentation"
    ARCHITECTURE = "architecture", "Architecture"
    SPECTRAL = "spectral", "EEG Spectral & Band Power"
    COMPLEXITY = "complexity", "EEG Complexity"
    MICROSTRUCTURE = "microstructure", "Microstructure"
    RESPIRATORY = "respiratory", "Muscle & Respiration"
    CUSTOM = "custom", "Experimental / Custom"

class MetricDefinition(models.Model):
    key = models.CharField(max_length=64, primary_key=True, help_text="Identifier matching metrics_data key")
    display_name = models.CharField(max_length=128)
    category = models.CharField(max_length=30, choices=MetricCategory.choices, db_index=True)
    unit = models.CharField(max_length=32, blank=True, default="")
    
    normal_min = models.FloatField(null=True, blank=True)
    normal_max = models.FloatField(null=True, blank=True)
    
    is_editable = models.BooleanField(default=True, help_text="Allows doctor manual adjustment")
    is_active = models.BooleanField(default=True)
    show_in_report = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=100)

    class Meta:
        db_table = "metrics_metricdefinition"
        ordering = ("category", "display_order", "key")
```

---

### 4.7 `apps.reports.models.report`
Clinical narrative report and sign-off.

```python
import uuid
from django.db import models

class ClinicalReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    study = models.OneToOneField("studies.SleepStudy", on_delete=models.CASCADE, related_name="clinical_report")
    
    llm_model_name = models.CharField(max_length=128, default="opencode/default")
    executive_summary = models.TextField()
    architecture_findings = models.TextField()
    respiratory_and_micro_notes = models.TextField()
    differential_diagnoses = models.JSONBField(default=list)
    clinical_recommendations = models.JSONBField(default=list)
    
    physician_notes = models.TextField(blank=True, default="")
    is_signed_off = models.BooleanField(default=False, db_index=True)
    signed_off_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reports_clinicalreport"
        ordering = ("-created_at",)
```

---

### 4.8 `apps.assistant.models.chat_session` & `chat_message`
Interactive consultation sessions between physician and OpenCode LLM.

```python
import uuid
from django.db import models
from django.conf import settings

class ChatSender(models.TextChoices):
    PHYSICIAN = "physician", "Physician (Doctor)"
    ASSISTANT = "assistant", "AI Assistant (OpenCode)"
    SYSTEM = "system", "System Context"

class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    study = models.ForeignKey("studies.SleepStudy", on_delete=models.CASCADE, related_name="chat_sessions")
    physician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions")
    opencode_session_id = models.CharField(max_length=128, blank=True, default="")
    title = models.CharField(max_length=200, default="Study Clinical Consultation")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assistant_chatsession"
        ordering = ("-created_at",)

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    session = models.ForeignKey("assistant.ChatSession", on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=20, choices=ChatSender.choices, default=ChatSender.PHYSICIAN)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assistant_chatmessage"
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]
```

---

## 5. API Endpoints for File Inspection & Manual Overrides

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/studies/{id}/files/` | List all extracted files (epoch reports, raw recordings, annotations) |
| `GET` | `/api/v1/studies/{id}/files/{file_id}/` | Get file metadata and signal preview |
| `GET` | `/api/v1/studies/{id}/files/{file_id}/download/` | Download raw file |
| `PATCH` | `/api/v1/studies/{id}/epochs/{epoch_index}/override/` | Override single epoch stage (logs original vs corrected) |
| `POST` | `/api/v1/studies/{id}/epochs/bulk-override/` | Bulk override range of epochs (e.g., epochs 120–160 to N2) |
| `POST` | `/api/v1/studies/{id}/metrics/override/` | Manually adjust specific metrics with clinical rationale |
| `POST` | `/api/v1/studies/{id}/metrics/recalculate/` | Re-compute dependent metrics and SQI score after epoch/metric edits |
| `POST` | `/api/v1/studies/{id}/metrics/reset/` | Revert metrics to initial AI-generated baseline |
