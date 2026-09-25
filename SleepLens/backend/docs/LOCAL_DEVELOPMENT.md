# Local development

Backend for SleepLens: sleep stage classification + sleep depth / quality
index for uploaded PSG recordings.

## Requirements

- Python 3.10–3.12 — this machine runs the **system Python** (3.10.4) with the
  full stack already installed: Django 5.2, DRF, simplejwt, drf-spectacular,
  celery + redis client, structlog, psycopg, and the ML stack (torch, numpy,
  scipy, pandas, scikit-learn, lightgbm, pyedflib, mne, yasa).
- Docker (optional) for Postgres + Redis.

No virtualenv is used. Install/refresh the app's own dependencies with:

```powershell
cd SleepLens/SleepLens/backend
copy .env.example .env          # edit secrets / DB choice
python -m pip install -e ".[dev]"
python manage.py makemigrations accounts studies
python manage.py migrate
python manage.py createsuperuser
```

### Database choice

- `DB_ENGINE=postgres` (default): start the containers first —
  `docker-compose -f compose/dev/docker-compose.yml up -d` — then migrate.
- `DB_ENGINE=sqlite`: no containers needed; fine for a quick look.

### Queue choice

- Redis + Celery (default): start `redis` from the compose file, then run the
  API (`make run`) and a worker (`make worker`) in separate terminals.
- No Redis: set `CELERY_TASK_ALWAYS_EAGER=1` and `REDIS_ENABLED=0`. Uploads
  will then block until the night is analyzed (1–3 minutes per night on CPU).

## Model weights

Copy the two checkpoints into `analysis_weights/` as described in
`analysis_weights/MANIFEST.md`. Without them the upload endpoint still works
and the study is marked `failed` with a clear message.

## Tests

```powershell
make test                                  # full suite
make test-app APP=accounts                 # one app
python -m pytest apps/analysis -v
```

The pipeline smoke test generates a synthetic EDF and runs the real models;
it is skipped when the weights are missing.

## Endpoints (v1)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/accounts/register/` | create account, returns JWT (cookies + body) |
| POST | `/api/v1/accounts/login/` | login |
| POST | `/api/v1/accounts/token/refresh/` | refresh access token |
| POST | `/api/v1/accounts/logout/` | blacklist refresh token, clear cookies |
| GET  | `/api/v1/accounts/me/` | current user |
| GET/POST | `/api/v1/patients/` | list (`?search=`) / create patients |
| GET/PATCH | `/api/v1/patients/{id}/` | patient detail / update |
| POST | `/api/v1/studies/` | upload a study (EDF; optional `patient`, full `psqi` JSON) |
| GET  | `/api/v1/studies/` | list + filters (`search`, `status`, `date_from`, `date_to`, `ordering`) |
| GET  | `/api/v1/studies/{id}/` | study detail + status |
| GET  | `/api/v1/studies/{id}/night/` | night summary (stage table, review load, SDI metrics, window) |
| GET  | `/api/v1/studies/{id}/ssc/` | **per-frame staging**: stage, probabilities, confidence, band, needs_review |
| GET  | `/api/v1/studies/{id}/sdi/` | **per-frame sleep depth**: sdi 0-1 + REM flag |
| GET  | `/api/v1/studies/{id}/features/ssc/` | features derived from the staging stream |
| GET  | `/api/v1/studies/{id}/features/sqi/` | features derived from the depth model (RB/AP/CV/SK/MDR/PR/APEn/DFA) |
| GET/PUT/DELETE | `/api/v1/studies/{id}/psqi/` | get / set / remove the PSQI questionnaire (all-or-nothing) |
| GET  | `/api/v1/studies/{id}/report/` | latest generated markdown report |
| POST | `/api/v1/studies/{id}/report/generate/` | generate a new LLM markdown report |
| GET  | `/api/v1/studies/{id}/signals/` | channel list + decimated preview of the actual recording (`channels`, `start_sec`, `duration_sec`, `max_points`) |
| GET  | `/api/v1/studies/{id}/signals/{epoch}/` | one 30-s epoch waveform (`channels`, `points`) |
| GET  | `/api/v1/studies/{id}/download/` | download the uploaded recording file |
| GET/POST/DELETE | `/api/v1/studies/{id}/chat/` | assistant consultation session + history / create / reset |
| POST | `/api/v1/studies/{id}/chat/messages/` | send an expert question → assistant reply |
| GET  | `/api/v1/studies/{id}/chat/suggested-prompts/` | data-driven question chips |
| POST | `/api/v1/studies/{id}/reprocess/` | re-run the analysis |

### Assistant backend (opencode)

The consultation chat is powered by a **local opencode agent server**:

```bash
opencode serve --port 4096        # or: opencode web
```

- Default model for this project (free OpenCode Zen plan):
  `OPENCODE_MODEL=opencode/muse-spark-1.3-contributor-free`
  (any `providerID/modelID` from `GET /provider` works).
- Set `OPENCODE_BASE_URL` if the server listens elsewhere (default
  `http://127.0.0.1:4096`).
- When the server is not running, chat endpoints return
  `503 OPENCODE_UNAVAILABLE` — by design, there is no fake fallback.
- `OPENCODE_API_KEY` adds a bearer header for servers that enforce auth.
- Model errors are surfaced verbatim (e.g. a provider outage names the
  provider/model instead of a generic failure).

Health: `GET /api/health/`. OpenAPI: `/api/schema/`, Swagger UI `/api/docs/`.

## Dataset ingest (optional)

```powershell
python manage.py ingest_sleep_edf --owner-email you@example.com `
    --edf-root C:/SBU/Extra/Hachaton-Aiif/sleep-edf-dataset/sleep-edf-database-expanded-1.0.0 `
    --subsets both
```

Creates one patient per subject and one study per recording, stores the expert
hypnogram as ground truth, and keeps the EDFs where they are (`source_path`).
Analysis runs on demand via the `reprocess` endpoint (one night ≈ 2-3 min CPU).

## Confidence semantics (per-epoch report)

`confidence` is the max class probability. Bands come from settings:

- `high` (>= `CONFIDENCE_HIGH`, default 0.80) — label accepted as-is
- `medium` (>= `CONFIDENCE_MEDIUM`, default 0.60) — review recommended
- `low` (< 0.60) — suspicious, flagged `needs_review: true`

Calibration evidence from development: epochs with confidence > 0.9 were
99.5% correct; below 0.4 only ~43%. The timeline payload exposes the full
probability vector per epoch so a reviewer can inspect every decision.

## Not-assessable features

Some night features cannot be computed from a given recording (missing
airflow channel, 1-Hz envelope too coarse, absent movement annotations).
Those keys are **omitted from `values`** and listed in `not_assessable` with
a reason; never present an absent sensor as a good score.
