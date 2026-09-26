# SleepLens — AI-Powered Clinical Decision-Support System for Sleep Medicine

> A modern, end-to-end clinical platform engineered for somnologists (sleep specialists) to analyze patient Polysomnography (PSG) signals, review automated 5-class sleep staging, compute comprehensive Sleep Quality Index (SQI) metrics, generate bilingual AI diagnostic reports, and conduct interactive case consultations via local LLM.

---

## 📑 Table of Contents
- [1. System Architecture & Features](#1-system-architecture--features)
- [2. Quick Start for Team Members](#2-quick-start-for-team-members)
- [3. Step-by-Step Manual Installation](#3-step-by-step-manual-installation)
- [4. Working with the Sleep-EDF Dataset](#4-working-with-the-sleep-edf-dataset)
- [5. Patient-Segregated Repository (`data/sleep_edf_by_patient/`)](#5-patient-segregated-repository)
- [6. OpenCode Local LLM Integration](#6-opencode-local-llm-integration)
- [7. Clinical Decision Workstation Overview](#7-clinical-decision-workstation-overview)
- [8. Repository Structure](#8-repository-structure)
- [9. Testing & Quality Assurance](#9-testing--quality-assurance)

---

## 1. System Architecture & Features

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Sleep Specialist (Doctor)                         │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                 React + TypeScript Clinical Workstation (Port 3000)          │
│  • Patient Dashboard & Ingestion Wizard   • Interactive Hypnogram (AASM)    │
│  • Dynamic SQI Radial Gauge & Cards       • AI Persian Diagnostic Report     │
│  • PDF Export with Clinical Letterhead    • Real-Time Token Streaming Chat   │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ REST / SSE API
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Django 5.2 + DRF Backend Core (Port 8000)                 │
│  • Modular Domain Apps (Patients, Studies, Hypnograms, Metrics, Assistant)   │
│  • Zero-Migration Dynamic Metrics Engine (JSONB + GIN indexing)              │
│  • In-Process Asynchronous Pipeline Runner (ThreadPoolExecutor)              │
└──────────────────┬───────────────────┬───────────────────┬───────────────────┘
                   │                   │                   │
                   ▼                   ▼                   ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │  Sleep-EDF PSG  │ │ SQI 7-Category  │ │  OpenCode LLM   │
          │ Ingestion Engine│ │ Metrics Engine  │ │ Server (:4096)  │
          └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Core Clinical Capabilities:
- **5-Class Sleep Staging**: Interactive step-line hypnogram mapping 30s epochs into `Wake`, `N1`, `N2`, `N3` (Deep Slow-Wave), and `REM` (Dream Sleep), complete with click-to-override physician corrections.
- **7-Category Sleep Quality Index (SQI)**: Dynamic calculation of Continuity, Fragmentation, Architecture, Spectral Power, Microstructure (spindles, slow waves, arousals), Muscle & Breathing, and composite 0–100 SQI score.
- **Dedicated Patient Repositories**: Every patient has a dedicated, self-contained directory containing their raw archives, extracted brainwave signals, staging JSONs, and reports.
- **Persian AI Diagnostic Generator**: Automated extraction of patient context and metrics into professional Persian medical reports featuring ICD-10 differential diagnoses and evidence-based therapeutic recommendations.
- **Interactive Somnologist Chat Assistant**: Pre-injected patient context allowing doctors to query specific epochs, brainwave frequencies, and patient findings with real-time SSE token streaming.

---

## 2. Quick Start for Team Members

### Prerequisites
Before running, make sure your machine has:
- **Python 3.10+** (Python 3.11 or 3.12 recommended)
- **Node.js 18+** & **npm**
- **Git**

### Automated Setup (One-Click)
Clone the repository and run the setup script:

```bash
git clone <repository_url>
cd SleepLens

# Run the automated setup script:
./setup.sh
```

### Start the Application
To run both backend and frontend together:

```bash
cd webapp
./run_all.sh
```

Visit **`http://127.0.0.1:3000`** in your browser to access the workstation!

---

## 3. Step-by-Step Manual Installation

If you prefer to configure components manually:

### Step 1: Backend Setup
```bash
# Navigate to webapp
cd webapp

# 1. Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Seed the clinical metric definitions catalog
python manage.py seed_metrics

# 5. (Optional) Create superuser for Django Admin
python manage.py createsuperuser
```

### Step 2: Frontend Setup
```bash
# In a new terminal:
cd webapp/frontend

# Install node dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend will start on **`http://127.0.0.1:3000`** and proxy API calls to the backend on **`http://127.0.0.1:8000`**.

---

## 4. Working with the Sleep-EDF Dataset

The project is built on the real **Sleep-EDF Database Expanded (v1.0.0)** (197 whole-night Polysomnography recordings across 100 subjects).

### Ingesting Real Data into the Database
To import all 197 Polysomnography studies and their ground-truth expert hypnograms into SleepLens:

```bash
cd webapp
.venv/bin/python manage.py ingest_sleep_edf
```

#### Ingestion Options:
- `--limit N`: Ingest only the first `N` recordings (e.g., `--limit 10` for quick testing).
- `--regime cassette|telemetry|all`: Ingest specific sub-study (default `all`).
- `--no-trim`: Keep the full 24-hour raw recording without trimming to the standard in-bed sleep window.

---

## 5. Patient-Segregated Repository (`data/sleep_edf_by_patient/`)

The ingestion pipeline automatically segregates files per patient under `data/sleep_edf_by_patient/` without modifying the original raw dataset:

```
data/sleep_edf_by_patient/
├── SC400/
│   ├── SC4001E0-PSG.edf             (Night 1 PSG raw signals)
│   ├── SC4001EC-Hypnogram.edf       (Night 1 ground-truth annotations)
│   ├── SC4002E0-PSG.edf             (Night 2 PSG raw signals)
│   ├── SC4002EC-Hypnogram.edf       (Night 2 ground-truth annotations)
│   └── patient_metadata.json        (Demographics, nights, lights-off times)
├── SC401/
└── ST701/
    ├── ST7011J0-PSG.edf
    ├── ST7011JP-Hypnogram.edf
    └── patient_metadata.json        (Placebo vs. Temazepam trial conditions)
```

---

## 6. OpenCode Local LLM Integration

SleepLens integrates with your local OpenCode agent server on **`http://127.0.0.1:4096`**.

### Starting OpenCode Server
In a separate terminal, start your local OpenCode instance:
```bash
opencode serve --port 4096
# Or if using web UI:
opencode web --port 4096
```

- **Offline Fallback**: If OpenCode is not running, SleepLens gracefully falls back to built-in clinical templates. All tabs and features remain 100% operational.
- **Patient Context Injection**: When OpenCode is queried from a patient's study workstation, it receives the exact disk path to the patient's directory (`webapp/media/patients/{MRN}/study_{ID}/`) and direct summaries of all signals, hypnogram predictions, and SQI metrics.

---

## 7. Clinical Decision Workstation Overview

When viewing a patient's study on `http://127.0.0.1:3000`:

1. **Tab 1: کاوشگر فایل‌ها (File Explorer)**: Full file transparency showing raw archives, epoch signal JSONs, sensor channels (`EEG Fpz-Cz`, `EEG Pz-Oz`, `EOG`, `EMG`, `Resp`), and SHA-256 hashes.
2. **Tab 2: هایپنوگرام تعاملی (Interactive Hypnogram)**: Full-night step-line hypnogram with zoom, pan, confidence score markers, and click-to-edit stage override modal.
3. **Tab 3: شاخص کیفیت خواب و متریک‌ها (SQI & Dynamic Metrics)**: Radial dial (0–100 score), categorized metric cards, normal/borderline/abnormal status badges, manual metric override, and on-demand SQI recalculation.
4. **Tab 4: گزارش تشخیصی هوش مصنوعی (AI Clinical Report)**: Toggle between structured cards and full narrative Markdown report in Persian, ICD-10 differential diagnoses, actionable recommendations, physician notes, official sign-off, and **چاپ / خروجی رسمی PDF** with clinical letterhead.
5. **Floating Assistant Drawer (دستیار هوشمند طب خواب)**: Collapsible slide-out consultation drawer with pre-loaded patient data, suggested prompt chips, and real-time SSE token streaming.

---

## 8. Repository Structure

```
SleepLens/
├── setup.sh                         # One-click automated setup script for team members
├── requirements.txt                 # Unified root Python dependencies
├── README.md                        # Master repository documentation (this file)
├── TEAM_QUICKSTART_GUIDE.md         # Step-by-step onboarding guide for teammates
├── TEAM_QUICKSTART_GUIDE_FA.md      # Persian onboarding guide (راهنمای گام‌به‌گام هم‌تیمی‌ها)
├── DATABASE_SCHEMA.md               # Detailed database models and JSONB architecture
├── SQI_METRICS.md                   # 7 clinical categories and mathematical formulas
├── PHASE_BY_PHASE_ROADMAP.md        # 8-phase implementation roadmap & test plan
│
├── data/
│   └── sleep_edf_by_patient/        # Segregated patient directories (EDFs + metadata)
│
├── sleep-edf-database-expanded-1.0.0/ # Pristine raw dataset (197 recordings)
│   ├── sleep-cassette/              # 153 ambulatory home recordings
│   └── sleep-telemetry/             # 44 hospital inpatient trial recordings
│
├── webapp/                          # Core Django + React Web Application
│   ├── manage.py
│   ├── requirements.txt             # Backend dependencies
│   ├── run_all.sh                   # Startup script (starts backend & frontend)
│   ├── start_backend.sh             # Starts Django server on port 8000
│   ├── start_frontend.sh            # Starts Vite dev server on port 3000
│   │
│   ├── config/                      # Django project configuration (base/dev/prod)
│   ├── apps/                        # Modular Django domain apps
│   │   ├── patients/                # Patient model (UUIDv7, MRN, demographics)
│   │   ├── studies/                 # SleepStudy & StudyFile models
│   │   ├── hypnograms/              # SleepEpoch model (AASM 5-class staging)
│   │   ├── metrics/                 # StudyMetricsSummary (zero-migration JSONB)
│   │   ├── reports/                 # ClinicalReport model (Persian narrative + ICD-10)
│   │   └── assistant/               # ChatSession & ChatMessage models
│   │
│   ├── infrastructure/              # External service adapters (decoupled from Django)
│   │   ├── storage/                 # ZipExtractor & PatientStorageService
│   │   ├── staging_service/         # 5-class sleep staging client
│   │   ├── metrics_service/         # 7-category SQI calculation client
│   │   ├── opencode/                # OpenCode LLM client (prompting & parsing)
│   │   └── runners/                 # ThreadRunner in-process task pipeline
│   │
│   ├── frontend/                    # Modern React SPA
│   │   ├── package.json
│   │   ├── vite.config.ts           # Configured with polling watch (no ENOSPC)
│   │   └── src/
│   │       ├── components/          # Workstation tabs (Files, Hypno, Metrics, Report, Chat)
│   │       └── services/            # Axios API client & SSE streaming
│   │
│   └── tests/                       # Automated pytest test suites
│       ├── test_phase1_models.py
│       ├── test_phase2_adapters.py
│       ├── test_phase3_api.py
│       ├── test_phase4_llm.py
│       └── test_phase8_e2e.py
```

---

## 9. Testing & Quality Assurance

To run the full automated test suite:

```bash
cd webapp

# Run all 28 automated tests across all 8 phases:
.venv/bin/pytest tests/

# Run standalone end-to-end verification script:
.venv/bin/python verify_phase8_e2e.py
```

All 28 tests pass with 100% coverage across models, adapters, REST APIs, LLM generation, and end-to-end Polysomnography lifecycle.
