# SleepLens — Master Architectural Plan & Technical Roadmap (English)

## 1. Executive Summary & Vision

**SleepLens** is an AI-powered clinical decision-support platform designed specifically for sleep medicine specialists (somnologists). The platform streamlines the diagnostic workflow by:
1. **Ingesting Patient Polysomnography (PSG) Data**: Accepting ZIP archives containing 30-second epoch reports or raw `.edf` / `.epf` recordings.
2. **Transparent File & Epoch Inspection**: Every file inside the patient's archive (raw signals, individual 30-second epoch reports, technician annotations, demographics) is indexed and inspectable. Physicians can review raw signal snippets, inspect individual epoch reports, and download files directly.
3. **Automated Sleep Staging with Physician Override**: Delegating 30-second epoch staging to an external AI model/service while empowering the physician to review and manually correct any misclassified epoch (preserving an audit trail between `ai_predicted_stage` and `stage`).
4. **Dynamic Metric Extraction & SQI with Manual Adjustment**: Computing core sleep quality metrics (Continuity, Fragmentation, Architecture, EEG Band Power, EEG Complexity, Microstructure, Muscle & Breathing) and generating a unified **Sleep Quality Index (SQI)** as specified in `SQI_METRICS.md`. **The metrics architecture is fully dynamic** (PostgreSQL JSONB + GIN indexing + Metric Definition Catalog). Furthermore, physicians can manually adjust metrics if artifacts or clinical nuances require it, triggering an **on-demand recalculation** of dependent metrics and SQI.
5. **AI-Powered Narrative Clinical Reports**: Generating structured clinical evaluations, differential diagnoses, and actionable recommendations through an OpenCode LLM agent.
6. **Interactive Doctor-LLM Consultation**: Providing a real-time, context-aware chat session where the physician can interrogate the model regarding patient findings, anomalies, and customized treatment plans.

---

## 2. High-Level System Architecture

```
                               ┌────────────────────────────────┐
                               │        Sleep Specialist        │
                               │           (Physician)          │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                      ┌──────────────────────────────────────────────────┐
                      │             SleepLens Frontend (SPA)             │
                      │   (React + TypeScript + Tailwind + Recharts)     │
                      │                                                  │
                      │  • File & Epoch Explorer                         │
                      │  • Interactive Hypnogram & Stage Override Editor │
                      │  • Dynamic Metric Cards with Clinical Edit Modal │
                      │  • Recalculate SQI On-Demand Button              │
                      │  • OpenCode Real-Time Chat Drawer                │
                      └─────────┬───────────────────────────────┬────────┘
                                │ REST APIs                     │ SSE Chat Stream
                                ▼                               ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              Django 6.0+ Backend Core                                  │
│                                                                                        │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │   apps/studies   │───▶│ apps/hypnograms  │───▶│           apps/metrics           │  │
│  │  (Files & ZIP)   │    │(Staging&Override)│    │(Dynamic JSONB & Recalculation)   │  │
│  └────────┬─────────┘    └──────────────────┘    └────────────────┬─────────────────┘  │
│           │                                                       │                    │
│           │ In-process ThreadPool execution                       ▼                    │
│           ▼                                      ┌──────────────────────────────────┐  │
│  ┌──────────────────┐                            │           apps/reports           │  │
│  │ In-Process Async │                            │  (Clinical Summaries & Sign-off) │  │
│  │  Task Runner     │                            └────────────────┬─────────────────┘  │
│  │ (ThreadPoolExec) │                                             │                    │
│  └────────┬─────────┘                                             │                    │
│           │                                                       ▼                    │
│           │ Pipeline Orchestration               ┌──────────────────────────────────┐  │
│           │                                      │          apps/assistant          │  │
│           │                                      │   (Doctor-LLM Chat Sessions)     │  │
│           │                                      └────────────────┬─────────────────┘  │
│           ▼                                                       ▼                    │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                     Infrastructure Adapters (Anti-Corruption)                    │  │
│  │  ┌─────────────────────┐   ┌─────────────────────┐   ┌────────────────────────┐  │  │
│  │  │ Staging AI Service  │   │   Metrics Engine    │   │  OpenCode LLM Client   │  │  │
│  │  │ (30s Epoch Model)   │   │(SQI & Recalculator) │   │ (Local Port 4096 API)  │  │  │
│  │  └─────────────────────┘   └─────────────────────┘   └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬─────────────────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌────────────────────────┐                             ┌────────────────────────┐
│  PostgreSQL Database   │                             │   File / Object Store  │
│  (Relational & JSONB)  │                             │ (Extracted Epoch Files)│
└────────────────────────┘                             └────────────────────────┘
```

---

## 3. Backend Architecture (Django 6.0+ & DRF)

The backend adheres strictly to `backend_coding_guidelines/`:
- **File Size & Cohesion**: Files target ≤ 200 lines (300 max). Single responsibility per file (one model per file, one serializer per file).
- **Lightweight Async Task Runner (No Celery Complexity)**: In-process background thread runner using Python's built-in `concurrent.futures.ThreadPoolExecutor` (`infrastructure/runners/thread_runner.py`). No Redis or Celery daemons required.
- **Human-in-the-Loop Architecture**:
  - `StudyFile`: Maps every file in the patient ZIP (raw EDFs, 30s epoch reports, annotations, metadata) with preview data and download support.
  - `SleepEpoch`: Retains both `ai_predicted_stage` (original) and `stage` (effective stage editable by physician).
  - `StudyMetricsSummary`: Preserves `ai_raw_metrics` alongside active `metrics_data` and tracks adjustments in `overrides` and `MetricOverride` audit rows.
  - `RecalculationEngine`: Recalculates dependent metrics (Sleep Efficiency, WASO, SFI, SQI score) when the physician edits stages or metrics.

### 3.1 Folder Structure
```
SleepLens-backend/
├── config/                      # Project settings & ASGI/WSGI
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── asgi.py
│   └── urls.py
├── apps/
│   ├── accounts/                # Doctor authentication and roles
│   ├── patients/                # Patient demographics & history
│   ├── studies/                 # Study upload, extracted files explorer, state machine
│   ├── hypnograms/              # 30-sec epoch stages, manual stage overrides, transitions
│   ├── metrics/                 # Dynamic SQI, metric catalog, physician overrides & recalculator
│   ├── reports/                 # Clinical narrative reports & PDF export
│   └── assistant/               # Doctor-LLM chat sessions & messages
├── infrastructure/              # External service adapters & runners
│   ├── runners/                 # In-process background ThreadRunner
│   ├── staging_service/         # 30s epoch staging model client
│   ├── metrics_service/         # Dynamic SQI & spectral computation client
│   ├── opencode/                # Local OpenCode LLM client (port 4096)
│   └── storage/                 # Safe ZIP extractor & file explorer
├── common/                      # Shared base models, standard responses, pagination
└── manage.py
```

---

## 4. Frontend Architecture (React + TypeScript)

### 4.1 Key Clinical User Interface Views
1. **Studies Dashboard (`/studies`)**:
   - Table of all patient studies with status badges, SQI scores, and quick filters.
2. **Study Ingestion Wizard (`/studies/upload`)**:
   - Drag-and-drop ZIP upload with live progress tracker polling the backend state machine.
3. **Clinical Analysis Workstation (`/studies/:id`)**:
   - **Patient Files & Epoch Explorer Tab**:
     - Tree view of all files extracted from the ZIP.
     - Direct inspection of epoch reports, signal previews, and download links.
   - **Interactive Hypnogram Tab**:
     - 30-second epoch step chart with zoom, pan, and stage distribution charts.
     - **Click-to-Edit Stage**: Doctor can click an epoch or drag a range to change stage (e.g. Wake ➔ N1), showing visual diffs between AI prediction and doctor override.
   - **Dynamic SQI & Metric Breakdown Tab**:
     - Metric cards dynamically rendered from `MetricDefinition` metadata with normal/abnormal badges.
     - **"Edit Metric" Modal**: Allows the physician to adjust any metric with clinical rationale.
     - **"Recalculate SQI" Action**: Re-runs dependent calculations and updates the overall score.
   - **AI Clinical Report Tab**:
     - Markdown narrative report with differential diagnoses and recommendations.
     - Doctor notes section and PDF export.
   - **Assistant Chat Drawer**:
     - Slide-over drawer to chat with OpenCode LLM with patient context pre-loaded.

---

## 5. Phased Implementation Roadmap

- **Phase 1: Backend Foundation & Data Modeling**: Initialize Django 6.0+, configure PostgreSQL, implement domain models (`Patient`, `SleepStudy`, `StudyFile`, `SleepEpoch` with overrides, `StudyMetricsSummary`, `MetricOverride`, `MetricDefinition`, `ClinicalReport`, `ChatSession`) with migrations.
- **Phase 2: Ingestion & Infrastructure Adapters**: Safe ZIP extraction indexing each file into `StudyFile`, staging model adapter, dynamic SQI metrics adapter, and OpenCode client.
- **Phase 3: Async Task Runner, Overrides & REST APIs**: In-process task runner, stage override API, metric override & recalculation endpoints, and file explorer APIs.
- **Phase 4: OpenCode LLM Integration & Real-Time Chat**: Contextual clinical prompt engineering, chat session management, and SSE token streaming.
- **Phase 5: Frontend Core & Ingestion Wizard**: React + Vite setup, UI layout, TanStack Query integration, and multi-step upload wizard.
- **Phase 6: Frontend Hypnogram, File Explorer & Dynamic Metrics UI**: Interactive hypnogram with stage override modal, file explorer tree, dynamic metric cards, and recalculation button.
- **Phase 7: Frontend AI Report & Chat Drawer**: Markdown report viewer, physician sign-off, PDF export, and slide-over LLM chat drawer.
- **Phase 8: End-to-End Testing & Docker Setup**: Single-command containerization and end-to-end verification with sample PSG records.
