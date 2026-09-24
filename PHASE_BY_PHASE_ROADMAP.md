# SleepLens — Phase-by-Phase Implementation Roadmap & Testing Guide

This document is the actionable, step-by-step implementation guide for **SleepLens**. Every phase has defined deliverables, affected files, and exact test commands so that each step can be independently tested and verified before moving to the next.

---

## Progress Overview

| Phase | Description | Status | Verification Command |
|---|---|---|---|
| **Phase 1** | Backend Foundation, Data Models & Dynamic Schema | ✅ **COMPLETED** | `cd webapp && .venv/bin/python verify_phase1.py` |
| **Phase 2** | Ingestion Pipeline & External Service Adapters | ✅ **COMPLETED** | `cd webapp && .venv/bin/python verify_phase2.py` |
| **Phase 3** | In-Process Task Runner Pipeline & REST APIs | ✅ **COMPLETED** | `cd webapp && .venv/bin/python verify_phase3.py` |
| **Phase 4** | OpenCode LLM Clinical Report & Interactive Chat | ✅ **COMPLETED** | `cd webapp && .venv/bin/python verify_phase4_llm.py` |
| **Phase 5** | Frontend Core, Layout & Study Ingestion Wizard | ✅ **COMPLETED** | `cd webapp/frontend && npm run build` |
| **Phase 6** | Frontend Hypnogram, File Explorer & Dynamic Metrics | ✅ **COMPLETED** | Visual interactive verification in browser |
| **Phase 7** | Frontend AI Report Viewer & Real-Time Chat Drawer | ✅ **COMPLETED** | Real-time SSE streaming chat in browser UI |
| **Phase 8** | End-to-End Testing & Polysomnography Integration | ⏳ **NEXT UP** | Full pipeline end-to-end rehearsal |

---

## Detailed Breakdown of Each Phase

---

### Phase 1: Backend Foundation, Data Models & Dynamic Schema
> **Status**: ✅ **COMPLETED & VERIFIED**

#### 1. What was built:
- Dedicated virtual environment (`webapp/.venv`) and unified `requirements.txt`.
- Django 5.2 project structure adhering to `backend_coding_guidelines/` (`config/settings/base.py`, `dev.py`, `prod.py`).
- 6 domain applications inside `webapp/apps/`:
  - `apps.patients`: `Patient` model with UUIDv7, unique MRN, demographics.
  - `apps.studies`: `SleepStudy` (state machine) and `StudyFile` (file-by-file transparency).
  - `apps.hypnograms`: `SleepEpoch` with dual-stage tracking (`ai_predicted_stage` vs. `stage`) and per-epoch micro-metrics.
  - `apps.metrics`: `StudyMetricsSummary` (zero-migration JSONB dynamic metrics), `MetricDefinition` (catalog of 20 clinical metrics), and `MetricOverride` (audit log).
  - `apps.reports`: `ClinicalReport` model with differential diagnoses and recommendations.
  - `apps.assistant`: `ChatSession` and `ChatMessage` models for OpenCode interaction.
- `seed_metrics` management command pre-populating clinical metrics from `SQI_METRICS.md`.
- Schema Inspector script (`show_schema.py`) and admin superuser (`admin` / `admin123`).

#### 2. How to test:
```bash
cd webapp
# Run automated verification smoke test:
.venv/bin/python verify_phase1.py

# Run pytest unit tests:
.venv/bin/pytest tests/

# View schema in terminal:
.venv/bin/python show_schema.py

# Inspect in browser:
.venv/bin/python manage.py runserver
# Open http://127.0.0.1:8000/admin/
```

---

### Phase 2: Ingestion Pipeline & External Service Adapters
> **Status**: ✅ **COMPLETED & VERIFIED**

#### 1. Objective:
Build the decoupled adapter layer (`infrastructure/`) to safely extract patient ZIP archives, invoke external AI staging models, compute SQI metrics, and connect to OpenCode.

#### 2. Components & Files to Create:
- `infrastructure/storage/zip_extractor.py`:
  - Safe ZIP extraction with path traversal protection (`../` prevention).
  - File validation (checks for `.edf`, `.epf`, `.json`, `.npz`).
  - Indexing: automatically registers each extracted file as a `StudyFile` record in the database.
- `infrastructure/staging_service/client.py`:
  - Interface for 30-second epoch sleep staging.
  - Supports calling external Python models or fallback heuristics (predicts Wake, N1, N2, N3, REM with confidence scores).
- `infrastructure/metrics_service/client.py`:
  - Computes all 7 categories from `SQI_METRICS.md` (Continuity, Fragmentation, Architecture, Spectral, Microstructure, Respiration).
  - Calculates the composite **Sleep Quality Index (SQI)** score (0–100) and category (`OPTIMAL`, `GOOD`, `FAIR`, `POOR`).
- `infrastructure/opencode/client.py`:
  - Client communicating with the local OpenCode server (`http://127.0.0.1:4096`).
  - Session creation (`POST /session`) and prompt generation.

#### 3. How to test Phase 2:
```bash
cd webapp
# A dedicated test runner verifying extraction, staging, and metric computation on a sample patient file:
.venv/bin/python verify_phase2.py
```

---
### Phase 3: In-Process Task Runner Pipeline & REST APIs
> **Status**: ✅ **COMPLETED & VERIFIED**

#### 1. Objective:
Connect the ingestion and adapters into a lightweight, non-blocking background pipeline (without Celery) and expose RESTful APIs for the frontend.

#### 2. Components & Files to Create:
- `infrastructure/runners/thread_runner.py`:
  - Uses `concurrent.futures.ThreadPoolExecutor` to run the 4-step pipeline:
    1. Unpack ZIP ➔ 2. AI Staging ➔ 3. Compute Metrics & SQI ➔ 4. Draft AI Report.
  - Updates `SleepStudy.status` in the database at each step.
- `apps/studies/services/recalculation_service.py`:
  - Recalculates dependent metrics and SQI when a doctor manually edits epoch stages or metric values.
- REST API Serializers & ViewSets (`api/v1/`):
  - `POST /api/v1/studies/upload/`: Upload ZIP archive and kick off background processing.
  - `GET /api/v1/studies/{id}/status/`: Real-time status polling for progress bar.
  - `GET /api/v1/studies/{id}/files/`: List all extracted patient files with download URLs.
  - `GET /api/v1/studies/{id}/hypnogram/`: Retrieve all 30s epochs with stages and micro-metrics.
  - `PATCH /api/v1/studies/{id}/epochs/{epoch_index}/override/`: Doctor stage correction.
  - `GET /api/v1/studies/{id}/metrics/`: Dynamic metrics payload + catalog metadata.
  - `POST /api/v1/studies/{id}/metrics/override/`: Physician metric adjustment.
  - `POST /api/v1/studies/{id}/metrics/recalculate/`: On-demand SQI recalculation.

#### 3. How to test Phase 3:
```bash
cd webapp
.venv/bin/pytest tests/test_phase3_api.py
```

---
### Phase 4: OpenCode LLM Clinical Report & Interactive Chat
> **Status**: ✅ **COMPLETED & VERIFIED**

#### 1. Objective:
Integrate the local OpenCode LLM server to generate structured clinical summary reports and enable real-time doctor-LLM interactive consultations.

#### 2. Components & Files to Create:
- `apps/reports/services/prompt_builder.py`:
  - Prepares clinical context (Patient age, sex, medical history, SQI score, abnormal metrics, hypnogram anomalies).
- Report Generator:
  - Generates executive summary, differential diagnoses, and treatment recommendations into `ClinicalReport`.
- Doctor-LLM Chat Endpoints:
  - `POST /api/v1/studies/{id}/chat/`: Start or resume consultation session.
  - `POST /api/v1/studies/{id}/chat/{session_id}/message/`: Physician asks question.
  - `GET /api/v1/studies/{id}/chat/{session_id}/stream/`: Server-Sent Events (SSE) token streaming.

#### 3. How to test Phase 4:
```bash
cd webapp
.venv/bin/python verify_phase4_llm.py
```

---

### Phase 5: Frontend Core, Layout & Study Ingestion Wizard
> **Status**: 📋 **PLANNED**

#### 1. Objective:
Scaffold the React + TypeScript frontend, establish the clinical navigation shell, and build the multi-step study upload wizard.

#### 2. Components & Views:
- Setup: Vite + React 18/19 + TypeScript + Tailwind CSS + `shadcn/ui`.
- Global Layout: Navigation sidebar, header, patient context banner.
- Studies Dashboard (`/studies`): Table of patient studies with SQI score chips and status indicators.
- Ingestion Wizard (`/studies/upload`):
  - Step 1: Patient selection / registration.
  - Step 2: Drag-and-drop ZIP upload zone.
  - Step 3: Real-time progress bar polling `GET /api/v1/studies/{id}/status/`.

#### 3. How to test Phase 5:
```bash
cd webapp/frontend
npm run dev
```

---

### Phase 6: Frontend Hypnogram, File Explorer & Dynamic Metrics UI
> **Status**: 📋 **PLANNED**

#### 1. Objective:
Implement the primary clinical workstation for somnologists to examine files, review the hypnogram, and edit metrics.

#### 2. Components & Views:
- **Patient File Explorer Tab**:
  - Tree browser of all files extracted from the ZIP.
  - Preview card for each 30s epoch report (signal amplitude, dominant frequencies).
- **Interactive Hypnogram Tab**:
  - Step-line chart mapping all 30s epochs to AASM stages (Wake, N1, N2, N3, REM).
  - Zoom & Pan controls (zoom into a 10-minute snippet or view full 8 hours).
  - Click-to-Edit: Click an epoch to open the stage override modal (records reason and updates stage).
- **Dynamic SQI & Metrics Tab**:
  - SQI radial dial (0–100 score).
  - Categorized metric cards dynamically generated from backend `MetricDefinition` metadata.
  - Color-coded status badges: Green (Normal), Yellow (Borderline), Red (Abnormal).
  - "Edit Metric" modal + "Recalculate SQI" on-demand button.

#### 3. How to test Phase 6:
- Visual inspection in browser: zoom the hypnogram, correct an epoch stage, edit a metric value, and click "Recalculate SQI" to see the score update immediately.

---

### Phase 7: Frontend AI Report Viewer & Real-Time Chat Drawer
> **Status**: 📋 **PLANNED**

#### 1. Objective:
Deliver the narrative diagnostic report and the slide-out conversational assistant drawer.

#### 2. Components & Views:
- **Clinical Report Viewer**:
  - Markdown-rendered report with differential diagnoses and recommendations.
  - Physician editable notes section.
  - "Sign & Finalize" button + "Export to PDF" button.
- **OpenCode Assistant Drawer**:
  - Collapsible slide-over drawer accessible from any tab in the study workstation.
  - Real-time token streaming with typing animation.
  - Suggested clinical prompt chips.

#### 3. How to test Phase 7:
- Open the chat drawer in the browser, send a clinical inquiry, and watch the response stream in real-time.

---

### Phase 8: End-to-End Testing & Polysomnography Integration
> **Status**: 📋 **PLANNED**

#### 1. Objective:
Conduct a complete end-to-end rehearsal using real Sleep-EDF sample recordings from the dataset.

#### 2. Verification Steps:
1. Upload sample patient ZIP archive.
2. In-process runner processes the recording through extraction, staging, and metrics.
3. Review hypnogram and metrics on frontend.
4. Physician overrides an epoch stage and recalculates SQI.
5. Generate and sign off on the AI clinical report.
6. Conduct an interactive consultation with the OpenCode LLM assistant.
