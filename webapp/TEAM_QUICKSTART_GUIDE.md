# SleepLens — Teammate Quickstart & Onboarding Guide

> Step-by-step instructions for teammates to clone, configure, run, and test SleepLens on their local machines.

---

## ⚡ 1-Minute Quick Start

```bash
# 1. Clone your branch
git clone <repo_url> -b morteza
cd SleepLens

# 2. Run the automated setup script
./setup.sh

# 3. Launch both Backend & Frontend
cd webapp
./run_all.sh
```

Open your browser at:
- **Workstation UI:** `http://127.0.0.1:3000`
- **Backend API:** `http://127.0.0.1:8000`
- **Django Admin:** `http://127.0.0.1:8000/admin/` (Login: `admin` / `admin123`)

---

## 🛠 Prerequisites

Ensure your system has the following installed:
1. **Python 3.10, 3.11, or 3.12**
   ```bash
   python3 --version
   ```
2. **Node.js 18+ and npm**
   ```bash
   node -v
   npm -v
   ```
3. **OpenCode Server (Optional for Live AI Report Generation / Chat)**
   If you have OpenCode installed:
   ```bash
   opencode serve --port 4096
   ```
   *(Note: If OpenCode is not running, SleepLens automatically falls back to offline mode with built-in medical clinical templates; nothing crashes).*

---

## 📦 Step-by-Step Manual Setup

If you prefer to run each step manually:

### 1. Backend Setup
```bash
cd webapp

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows (cmd/PowerShell):
# .venv\Scripts\activate

# Upgrade pip & install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed the 20 clinical metric definitions & reference ranges
python manage.py seed_metrics
```

### 2. Frontend Setup
```bash
# In another terminal:
cd webapp/frontend

# Install node dependencies
npm install

# Start development server
npm run dev
```

---

## 🔬 Loading the Real Sleep-EDF Dataset

To ingest all 197 Polysomnography studies (100 patients) and their expert-annotated hypnograms into the database:

```bash
cd webapp

# Ingest all 197 recordings with ground-truth sleep stages
.venv/bin/python manage.py ingest_sleep_edf
```

This command will:
1. Parse patient demographics from `SC-subjects.xls` and `ST-subjects.xls`.
2. Create 100 `Patient` records and 197 `SleepStudy` records in the database.
3. Parse 238,773 30-second epochs with expert ground-truth sleep stages from the hypnograms.
4. Segregate files per patient into `data/sleep_edf_by_patient/{mrn}/` using zero-overhead hardlinks (without altering the raw dataset).

---

## 🧪 Running Automated Tests

To verify that everything is working properly on your system:

```bash
cd webapp

# Run all 28 automated tests:
.venv/bin/pytest tests/

# Run the Phase 8 End-to-End verification runner:
.venv/bin/python verify_phase8_e2e.py
```

---

## ❓ Troubleshooting Common Teammate Issues

### 1. `ENOSPC: System limit for number of file watchers reached`
- **Cause:** Linux kernel file watcher limit when Vite scans `node_modules` on mounted drives.
- **Solution:** Already configured in `webapp/frontend/vite.config.ts` using polling (`usePolling: true`). If you still encounter this on older Linux kernels, run:
  ```bash
  echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
  ```

### 2. Port Conflicts (8000 or 3000 in use)
- Check what process is using the port:
  ```bash
  lsof -i :8000
  lsof -i :3000
  ```
- Kill the process or start with an alternative port:
  ```bash
  python manage.py runserver 8001
  npm run dev -- --port 3001
  ```

### 3. OpenCode Connection Offline
- If OpenCode is not running on port 4096, all features will still work using built-in medical fallback templates.
- To connect a live LLM model:
  ```bash
  opencode serve --port 4096
  ```
