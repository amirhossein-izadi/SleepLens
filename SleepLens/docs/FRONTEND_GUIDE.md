# SleepLens — Frontend Integration Guide

Everything a frontend developer needs to build the SleepLens UI against the
backend. Authoritative source of truth for payload shapes is the live schema:
**Swagger UI at `http://127.0.0.1:8000/api/docs/`** — this document explains how
to *use* it. (The Next.js app in `frontend/` is scaffolded; this guide is
framework-agnostic and works with any fetch client.)

---

## 0. What the product is (one minute)

SleepLens is a **sleep-analysis assistant for a sleep expert** (clinician,
technologist, researcher). The registered **user is the expert/operator**; they
manage a roster of **patients** (subject records — patients do **not** log in)
and upload nightly PSG recordings. The backend runs two model families on each
uploaded test:

1. **SSC — sleep stage classification** (`Wake/N1/N2/N3/REM` per 30-s epoch,
   with per-class probabilities, confidence and a review flag), plus
   stage-derived night features.
2. **SQI — sleep depth model** (the published SDI transformer): a 0–1 depth
   index + REM flag per epoch, plus depth-derived night features
   (RB/AP/CV/SK/MDR/PR/APEn/DFA).

Then an LLM (`gpt-6-luna`) writes a **markdown report** per night.

### Object model
```
User (expert)  ──owns──▶  Patient (record: name, sex, birth_year, notes)
   │                          │
   └──uploads──▶ Study ◀──────┘        (one nightly test = one Study)
                   ├─ StudyEpoch[]     per-30-s result rows (stage + depth)
                   ├─ NightFeatures    both feature groups (ssc + sqi)
                   ├─ PSQI             optional questionnaire (all-or-nothing)
                   └─ ClinicalReport[] generated markdown reports (versioned)
```

Study status lifecycle: `uploaded → processing → completed | failed`.

---

## 1. Local setup

```bash
# backend (already implemented)
cd SleepLens/SleepLens/backend
python manage.py runserver 127.0.0.1:8000     # http://127.0.0.1:8000

# frontend dev server origin must be allowed; backend .env already has:
#   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
#   Next.js default port is 3000 -> allowed. Add others to .env if needed.
```

Useful during development:
- **Swagger UI:** `http://127.0.0.1:8000/api/docs/` (try every endpoint with auth)
- **Admin UI:** `http://127.0.0.1:8000/admin/` (create a superuser to browse data)
- **Demo account already exists** in the local dev DB (one processed night
  `SC4001E0-PSG.edf` with PSQI + generated report):
  `demo@sleeplens.local` / `demopass123`

Processing time: **~90–120 s per night** (CPU). With Redis/Celery the upload
returns immediately and the study moves `processing → completed`; in the
default dev config (eager) the upload request itself blocks for ~2 min — set
your client timeout to ≥ 180 s for `POST /studies/` in dev.

---

## 2. Auth (JWT: header + httpOnly cookies)

Tokens are returned in the body **and** set as httpOnly cookies
(`access_token`, `refresh_token`). Pick one transport:

- **Cookies (recommended for web):** `fetch(..., { credentials: "include" })`.
  No token handling in JS; the backend accepts them via `CookieJWTAuthentication`.
- **Header:** store `access` and send `Authorization: Bearer <access>`.

Access = 1 h, refresh = 7 days, **refresh rotates and blacklists the old
token** — always replace both tokens on refresh.

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/v1/accounts/register/` | `{email, password(≥8), full_name}` | 201 `{user, tokens}` |
| POST | `/api/v1/accounts/login/` | `{email, password}` | 200 `{user, tokens}` |
| POST | `/api/v1/accounts/token/refresh/` | `{}` (cookie) or `{refresh}` | 200 `{access, refresh}` |
| POST | `/api/v1/accounts/logout/` | `{}` | 200 `{detail}` + cookies cleared |
| GET | `/api/v1/accounts/me/` | — | 200 `user` |

```ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

const api = async (path: string, init: RequestInit = {}) => {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: init.body instanceof FormData
      ? init.headers
      : { "Content-Type": "application/json", ...(init.headers ?? {}) },
    ...init,
  });
  const body = await res.json();               // always the envelope, even for errors
  if (!res.ok) throw Object.assign(new Error(body.error?.message ?? "Request failed"), {
    status: res.status, code: body.error?.code, details: body.error?.details,
  });
  return body.data;
};
```

**401 handling:** try `POST /accounts/token/refresh/` once (cookies make this
automatic), then redirect to login. **429** = throttled (register 3/h,
login 10/min, uploads 20/h, report generation 10/h) — show a friendly retry
message.

---

## 3. Response envelope (every endpoint)

```jsonc
// success
{ "success": true, "data": { /* payload */ } }

// list (paginated)
{ "success": true,
  "data": [ /* rows */ ],
  "metadata": { "total": 42, "page": 1, "limit": 20, "pages": 3 } }

// error
{ "success": false, "data": null,
  "error": { "code": "VALIDATION_ERROR",
             "message": "Validation failed",
             "details": [{ "field": "file", "message": "Unsupported file type '.txt'." }] } }
```

Error codes you will meet: `VALIDATION_ERROR` (400), `UNAUTHORIZED` (401),
`FORBIDDEN` (403), `NOT_FOUND` (404), `CONFLICT` (409), `RATE_LIMITED` (429),
`LLM_UNAVAILABLE` (503), `INTERNAL_ERROR` (500).

---

## 4. Endpoint reference

### 4.1 Patients (full CRUD)

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/patients/?search=&ordering=` | list (paginated); `ordering` = `full_name` (default) · `-full_name` · `created_at` · `-created_at` |
| POST | `/api/v1/patients/` | `{full_name, birth_year?, sex?, notes?}` |
| GET / PUT / PATCH | `/api/v1/patients/{id}/` | detail / full update / partial update |
| DELETE | `/api/v1/patients/{id}/` | **204**; their studies are kept and unlinked (`Study.patient → null`) |
| GET | `/api/v1/patients/{id}/studies/` | all studies of one patient, newest first (patient page / report flow) |

```jsonc
// patient
{ "id": "uuid", "full_name": "Jane Doe", "birth_year": 1980,
  "sex": "female",                 // male | female | other | unknown
  "notes": "", "created_at": "…", "updated_at": "…" }
```

Patients are owner-scoped: another user's patient id returns **404**.

### 4.2 Studies — list, filter, upload

```
GET /api/v1/studies/?search=night&status=completed
    &date_from=2026-01-01&date_to=2026-12-31
    &ordering=-created_at&page=1&limit=20
```
`ordering` ∈ `created_at | -created_at (default) | original_filename | status`.

```jsonc
// a study row / detail
{ "id": "uuid",
  "original_filename": "night-PSG.edf",
  "file_size": 110457600,
  "download_url": "/api/v1/studies/<id>/download/",
  "status": "completed",                  // uploaded | processing | completed | failed
  "status_message": "Analysis complete.",
  "error_message": "",
  "patient": { "id": "uuid", "full_name": "Jane Doe", "sex": "female", "birth_year": 1980 } | null,
  "duration_minutes": 1325.0,
  "n_epochs": 2650,
  "summary": { /* night summary; see /night/ */ },
  "signal_quality": { /* channels, sample_rates, substitutions, analysis_window, … */ },
  "psqi_taken": true, "psqi_global_score": 6,
  "created_at": "…", "started_at": "…", "finished_at": "…" }
```

**Upload — `POST /api/v1/studies/` (`multipart/form-data`):**

| Field | Required | Rules |
|---|---|---|
| `file` | ✅ | `.edf`, ≤ 500 MB |
| `patient` | optional | UUID of your patient |
| `psqi` | optional | **JSON string** of the 7 PSQI component scores (Pittsburgh Sleep Quality Index; 0–3 each, all-or-nothing) |

```ts
const form = new FormData();
form.append("file", file);
if (patientId) form.append("patient", patientId);
if (psqiAnswers) form.append("psqi", JSON.stringify(psqiAnswers));
// psqiAnswers = { subjective_quality, sleep_latency, sleep_duration,
//                 habitual_efficiency, disturbances, medication_use, daytime_dysfunction }
```

PSQI UX rule: the questionnaire is **binary** — either all seven components are
filled (enable submit) or leave it untouched. Partial answers are rejected with
400. Components are each 0–3 (0 = best); the server computes the 0–21 global.

**Polling after upload:**
```ts
async function waitFor(studyId: string) {
  for (;;) {
    const study = await api(`/api/v1/studies/${studyId}/`);
    if (study.status === "completed" || study.status === "failed") return study;
    await new Promise((r) => setTimeout(r, 4000));
  }
}
```

`POST /api/v1/studies/{id}/reprocess/` re-runs the pipeline (use after changing
`STAGING_SYSTEM` on the server or to retry failures).

### 4.3 Results — six separate items (no big JSON)

All are `GET` and return `{success, data}`. Epochs are indexed **0..n-1**,
30 s each, aligned with the recording start, and are consistent across
`/ssc/`, `/sdi/`, `/signals/{epoch}/`.

#### a) `/studies/{id}/ssc/` — staging per frame (hypnogram + confidence chart)
```jsonc
{ "study_id": "…", "n_epochs": 2650, "epoch_seconds": 30,
  "stage_codes": { "Wake": 0, "N1": 1, "N2": 2, "N3": 3, "REM": 4 },
  "stage_labels": ["Wake", "N1", "N2", "N3", "REM"],
  "confidence_bands": { "high": 0.8, "medium": 0.6 },
  "frames": {
    "index":         [0, 1, …],
    "start_sec":     [0, 30, …],
    "stage":         [2, 2, 4, …],                     // code → label
    "probabilities": [[.05,.10,.70,.10,.05], …],       // [Wake,N1,N2,N3,REM]
    "confidence":    [0.70, 0.85, …],                  // max probability
    "confidence_band": ["medium","high", …],           // high ≥0.80 · medium ≥0.60 · low <0.60
    "needs_review":  [true, false, …]                  // band != high
  },
  "stage_summary": { "N2": { "count": 1162, "pct": 43.85,
                             "mean_confidence": 0.93, "review_count": 138 }, … },
  "review_summary": { "needs_review_count": 423, "needs_review_pct": 15.96,
                      "low_confidence_count": 0, "low_confidence_pct": 0.0 } }
```

#### b) `/studies/{id}/sdi/` — sleep depth per frame (depth curve)
```jsonc
{ "study_id": "…", "model": "sdi_transformer", "n_epochs": 2650, "epoch_seconds": 30,
  "sdi_range": [0.0, 1.0],
  "sdi_note": "higher = deeper; zero-shot research index (see substitutions)",
  "frames": { "index": […], "start_sec": […],
              "sdi": [0.62, 0.31, …],        // 0–1, may be null
              "rem_pred": [0, 1, …] },       // model REM head
  "sdi_stats": { "n": 2650, "mean": 0.60, "min": 0.002, "max": 0.999 },
  "substitutions": { "sdi_ecg_zero_filled": true, "sdi_emg_upsampled_from_1hz": true } }
```

#### c) `/studies/{id}/night/` — night summary card
```jsonc
{ "study_id": "…", "original_filename": "…", "status": "completed",
  "staging_system": "ensemble",
  "staging_members": ["anysleep_eeg_fpz+eeg_pz+eog", "anysleep_eeg_fpz",
                      "anysleep_eeg_pz", "lightgbm"],
  "analysis_window": { "start_epoch": 894, "end_epoch": 1816,
                       "start_sec": 26820, "end_sec": 54480 },
  "stage_counts": { "Wake": 2000, "N1": 52, … },
  "stage_pct":    { "Wake": 75.47, "N1": 1.96, … },   // of the whole recording
  "sleep_pct": 24.53,
  "mean_confidence": 0.9019,
  "needs_review_count": 423, "needs_review_pct": 15.96,
  "sdi_metrics": { "rb": 0.0862, "ap": 0.5982, "cv": 0.4991, "mdr": 0.3096, "pr": 0.1723 },
  "signal_quality": { "channels": { "eeg_fpz": "EEG Fpz-Cz", … },
                      "sample_rates": { … },
                      "substitutions": { … },
                      "analysis_window": { … },
                      "n_epochs_total": 2650, "sleep_epochs": 650 } }
```
The **analysis window** (first→last predicted sleep ±30 min) is what features
are computed over; the charts cover the full recording.

#### d) `/studies/{id}/features/ssc/` — features from the staging stream
```jsonc
{ "study_id": "…", "available": true, "group": "ssc",
  "source": { "staging_system": "ensemble", "staging_members": [ … ] },
  "values": {
    // continuity
    "tib_min": 396.0, "tst_min": 332.0, "se_pct": 72.0, "sol_min": 30.0,
    "waso_min": 99.0, "rem_lat_min": 123.0, "wake_pct_tib": 24.5,
    // architecture
    "n1_pct_tst": 8.0, "n2_pct_tst": 43.85, "n3_pct_tst": 27.69, "rem_pct_tst": 20.46,
    "n1_pct_first_half": …, "n1_pct_second_half": …, "rem_pct_first_half": …, "rem_pct_second_half": …,
    "n_rem_episodes": 5, "mean_rem_bout_min": 13.2,
    "longest_sleep_bout_min": …, "mean_sleep_bout_min": …,
    "longest_wake_post_onset_min": 30.0,
    // fragmentation
    "n_awakenings": 14, "awakening_index": 2.58, "n_stage_shifts": 96,
    "shift_index": 17.72, "sfi": 20.31, "arousal_count": …, "arousal_index": 5.54,
    // transitions (5×5 counts)
    "transitions": { "Wake": { "Wake": 12, "N1": 7, … }, "N1": { … }, … },
    // EEG spectral
    "abs_delta_mean": …, "rel_delta_mean": …, /* …all 5 bands, abs_*_mean + rel_*_mean */
    "swa_nrem_mean": …, "swa_sum": …, "rel_delta_nrem": …,
    "spec_entropy_wake": …, "spec_entropy_nrem": …, "spec_entropy_rem": …,
    "perm_entropy_wake": …, "perm_entropy_nrem": …, "perm_entropy_rem": …,
    // microstructure (YASA)
    "spindle_count_n2": …, "spindle_density_n2": …, "spindle_dur_mean": …,
    "spindle_freq_mean": …, "spindle_amp_mean": …,
    "sw_count_nrem": …, "sw_density_nrem": …, "sw_negamp_mean": …, "sw_dur_mean": …,
    // EMG
    "emg_median_uv": …, "emg_rem_mean_uv": …, "emg_nrem_mean_uv": …,
    "rem_atonia_ratio": …, "movement_index": …,
    "eeg_epochs_analyzed": 662 },
  "not_assessable": [
    { "key": "apnea_count", "reason": "Airflow channel is a low-rate envelope (~1 Hz); …" },
    { "key": "apnea_index", "reason": "…" },
    { "key": "apnea_time_pct", "reason": "…" },
    { "key": "move_annot_frac", "reason": "Movement/artefact annotations are not present …" } ] }
```

#### e) `/studies/{id}/features/sqi/` — features from the depth model
```jsonc
{ "study_id": "…", "available": true, "group": "sqi", "model": "sdi_transformer",
  "values": {
    "sdi_rb": 0.0862, "sdi_ap": 0.5982, "sdi_cv": 0.4991, "sdi_skew": 0.0402,
    "sdi_mdr": 0.3096, "sdi_pr": 0.1723,
    "sdi_mean_sleep": 0.5982, "sdi_std_sleep": 0.2986, "sdi_p05": 0.1416, "sdi_p95": 0.9979,
    "sdi_shallow_minutes": 28.0, "sdi_deep_minutes": 109.0, "sdi_auc": 194.4,
    "sdi_apen": 0.9689, "sdi_dfa": 1.3013 },
  "not_assessable": [], "substitutions": { … },
  "caveat": "SDI is a zero-shot research index (channel substitutions applied); not clinically validated." }
```

Combined view: `GET /studies/{id}/features/` →
`{ values: { ssc: {…}, sqi: {…} }, not_assessable: [...] }`.

#### f) PSQI (Pittsburgh Sleep Quality Index) — `GET | PUT | DELETE /studies/{id}/psqi/`
```jsonc
{ "taken": true, "global_score": 6,
  "components": { "subjective_quality": 1, "sleep_latency": 1, "sleep_duration": 0,
                  "habitual_efficiency": 1, "disturbances": 1,
                  "medication_use": 0, "daytime_dysfunction": 2 } }
```
PUT body: flat JSON with exactly those 7 integer keys (0–3). DELETE removes.
Global score = sum (0–21), computed server-side; 0 = good, higher = worse.

**Input format note:** the API stores the **seven component scores**, not the raw
19-question form. The questionnaire UI collects the raw questions in the
frontend and maps them to the 7 components client-side (standard PSQI scoring);
if you prefer the server to score raw answers, we can add that as a separate
field — ask before building that mapping twice.

#### g) Report — `GET /studies/{id}/report/` · `POST /studies/{id}/report/generate/`
```jsonc
{ "study_id": "…", "available": true,
  "markdown": "# Sleep report — SC4001E0-PSG.edf\n\n## Overview\n…",
  "model_name": "gpt-6-luna", "prompt_version": "v2",
  "generated_at": "2026-09-25T04:04:17Z" }
```
- Not generated yet → `{ available: false, markdown: null }`.
- Generate → `201` with the same shape (takes ~8–20 s → show a spinner);
  `503 LLM_UNAVAILABLE` if the server has no LLM key.
- Versioned: each generate appends; GET returns the latest.
- The report already includes patient info, PSQI (if taken), features, signal
  caveats and confidence/review points — do not re-derive numbers in the UI.
- Render with a markdown component (`react-markdown` + `remark-gfm`), style h2
  sections as cards.

### 4.4 Assistant consultation chat (opencode-backed)

The assistant is powered by a **local opencode agent server** (not the cloud LLM).
One consultation session per study; the case context is injected once at session
creation and the assistant is instructed to use only the provided values.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/studies/{id}/chat/` | session info + full message history |
| POST | `/api/v1/studies/{id}/chat/` | create (or re-fetch) the session — 503 `OPENCODE_UNAVAILABLE` if the server is down |
| DELETE | `/api/v1/studies/{id}/chat/` | reset the consultation |
| POST | `/api/v1/studies/{id}/chat/messages/` | `{content}` → `201` assistant reply (auto-creates the session) |
| GET | `/api/v1/studies/{id}/chat/suggested-prompts/` | data-driven question chips |

```jsonc
// GET /chat/ or POST /chat/
{ "study_id": "…", "available": true,
  "session": { "id": "uuid", "title": "SleepLens consultation — night-PSG.edf",
               "context_injected": true, "created_at": "…", "updated_at": "…" },
  "messages": [
    { "id": "…", "sender": "system",    "content": "You are the SleepLens clinical assistant… Case data (JSON): …" },
    { "id": "…", "sender": "user",      "content": "Why is N3 low?" },
    { "id": "…", "sender": "assistant", "content": "…" } ] }
```

- `sender` ∈ `system | user | assistant`; render `system` collapsed (it is the
  injected case context, useful for "what does the assistant know?").
- Availability is **binary**: if the opencode server is not running the endpoint
  returns `503 OPENCODE_UNAVAILABLE` — show a clear message, not a fake reply.
- Suggested prompts are computed from the actual night (SE, N3, SFI, shallow
  depth share, review %) and never suggest respiratory analysis when the airflow
  channel was not assessable.

### 4.5 Raw signals & uploaded material

```
GET /api/v1/studies/{id}/signals/?channels=EEG Fpz-Cz,EOG horizontal
    &start_sec=0&duration_sec=600&max_points=1200
```
```jsonc
{ "study_id": "…", "start_sec": 0, "duration_sec": 600,
  "file_duration_sec": 79500, "max_points": 1200,
  "channels": [ { "label": "EEG Fpz-Cz", "sample_rate": 100.0 } ],
  "available_channels": [ { "label": "…", "sample_rate": 100.0, "n_samples": 7950000 }, … ],
  "series": {
    "EEG Fpz-Cz":     { "t": [0, 0.01, …], "v": [12.3, -4.5, …] },       // kept raw when ≤ max_points
    "EOG horizontal": { "t": [0, 0.4, …], "min": [-9.1, …], "max": [8.7, …] } } }
```
- Decimation returns a **min/max envelope** (spikes preserved): draw a vertical
  band per `t` from `min` to `max`.
- Limits: ≤ 8 channels, `duration_sec` ≤ 3600, `max_points` ≤ 4000.
- Unknown channel name → `400` with the reason in `error.details`.

```
GET /api/v1/studies/{id}/signals/{epoch}/?channels=EEG Fpz-Cz,EOG horizontal&points=750
```
```jsonc
{ "study_id": "…", "epoch_index": 42, "start_sec": 1260, "duration_sec": 30,
  "channels": [ { "label": "EEG Fpz-Cz", "sample_rate": 25.0 } ],
  "series": { "EEG Fpz-Cz": { "t": [1260.0, 1260.04, …], "v": [ … ] } } }
```
`points` ≤ 3000 (default 750 = stride-averaged 25 Hz). Use this for the zoom
view; the `epoch_index` comes from clicking the hypnogram/depth chart
(`epoch = floor(t / 30)`).

```
GET /api/v1/studies/{id}/download/     → binary EDF attachment
```

---

## 5. TypeScript types (drop-in)

```ts
export type Stage = 0 | 1 | 2 | 3 | 4;                    // Wake N1 N2 N3 REM
export type ConfidenceBand = "high" | "medium" | "low";

export interface Envelope<T> { success: boolean; data: T; metadata?: PageMeta }
export interface PageMeta { total: number; page: number; limit: number; pages: number }

export interface User { id: string; email: string; full_name: string; is_active: boolean; created_at: string }
export interface Patient { id: string; full_name: string; birth_year: number | null;
                           sex: "male" | "female" | "other" | "unknown"; notes: string;
                           created_at: string; updated_at: string }

export interface Study {
  id: string; original_filename: string; file_size: number; download_url: string;
  status: "uploaded" | "processing" | "completed" | "failed";
  status_message: string; error_message: string;
  patient: Patient | null; duration_minutes: number | null; n_epochs: number | null;
  summary: NightSummary & { staging_system?: string }; signal_quality: SignalQuality;
  psqi_taken: boolean; psqi_global_score: number | null;
  created_at: string; started_at: string | null; finished_at: string | null;
}

export interface SscFrames {
  study_id: string; n_epochs: number; epoch_seconds: 30;
  stage_codes: Record<"Wake"|"N1"|"N2"|"N3"|"REM", Stage>;
  stage_labels: string[]; confidence_bands: { high: number; medium: number };
  frames: {
    index: number[]; start_sec: number[]; stage: Stage[];
    probabilities: [number, number, number, number, number][];
    confidence: number[]; confidence_band: ConfidenceBand[]; needs_review: boolean[];
  };
  stage_summary: Record<string, { count: number; pct: number;
                                  mean_confidence: number | null; review_count: number }>;
  review_summary: { needs_review_count: number; needs_review_pct: number;
                    low_confidence_count: number; low_confidence_pct: number };
}

export interface SdiFrames {
  study_id: string; model: string; n_epochs: number; epoch_seconds: 30;
  sdi_range: [number, number]; sdi_note: string;
  frames: { index: number[]; start_sec: number[]; sdi: (number | null)[]; rem_pred: (0|1|null)[] };
  sdi_stats: { n: number; mean: number | null; min: number | null; max: number | null };
  substitutions: Record<string, boolean>;
}

export interface NightSummary {
  study_id: string; original_filename: string; status: Study["status"];
  staging_system: string; staging_members: string[];
  analysis_window: { start_epoch: number; end_epoch: number; start_sec: number; end_sec: number };
  stage_counts: Record<string, number>; stage_pct: Record<string, number>;
  sleep_pct: number; mean_confidence: number;
  needs_review_count: number; needs_review_pct: number;
  sdi_metrics: { rb: number; ap: number; cv: number | null; mdr: number | null; pr: number };
  signal_quality: SignalQuality;
}
export interface SignalQuality {
  channels: Record<string, string>; sample_rates: Record<string, number>;
  substitutions: { sdi_ecg_zero_filled: boolean; sdi_emg_upsampled_from_1hz: boolean };
  analysis_window: { start_epoch: number; end_epoch: number; start_sec: number;
                     end_sec: number; n_epochs: number };
  n_epochs_total: number; sleep_epochs: number;
}
export interface NotAssessable { key: string; reason: string }

export interface FeatureGroup<T = Record<string, unknown>> {
  study_id: string; available: boolean; group: "ssc" | "sqi";
  values: T; not_assessable: NotAssessable[];
  source?: { staging_system: string; staging_members: string[] };
  model?: string; substitutions?: Record<string, boolean>; caveat?: string;
}

export type PsqiComponent = "subjective_quality" | "sleep_latency" | "sleep_duration"
  | "habitual_efficiency" | "disturbances" | "medication_use" | "daytime_dysfunction";
export interface Psqi { taken: boolean; global_score: number | null;
                        components: Partial<Record<PsqiComponent, number>> }

export interface Report { study_id: string; available: boolean; markdown: string | null;
                          model_name?: string; prompt_version?: string; generated_at?: string }

export interface SignalSeriesPoint { t: number[]; v?: number[]; min?: number[]; max?: number[] }
export interface SignalPreview {
  study_id: string; start_sec: number; duration_sec: number; file_duration_sec: number;
  max_points: number; channels: { label: string; sample_rate: number }[];
  available_channels: { label: string; sample_rate: number; n_samples: number }[];
  series: Record<string, SignalSeriesPoint>;
}
```

---

## 6. Screen map & flows

```
/login, /register
   │
   ▼
/  (Dashboard: study list)
   ├─ filters: search, status, date range, ordering; pagination
   ├─ row: filename · patient · status chip · created_at · confidence · review %
   └─ [Upload] ──▶ /studies/new (wizard)
                    1. choose patient (search `/patients/?search=`, or create inline)
                    2. drop/select .edf (progress bar; 500 MB max)
                    3. optional PSQI: toggle "Take PSQI" → 7 component selects
                       (all-or-nothing; disable submit until complete or off)
                    4. submit → redirect to /studies/{id} (status polling)

/patients, /patients/{id}   (roster + per-patient night history via /patients/{id}/studies/)
/studies/{id}  (tabs)
   ├─ Overview   : night summary card + stage donut + SDI metric chips + review banner
   ├─ Staging    : hypnogram + confidence ribbon (click epoch → Signals tab)
   ├─ Depth      : SDI curve (0–1) + REM markers + substitution caveat
   ├─ Signals    : waveform viewer (overview envelope, zoom to 30-s epoch)
   ├─ Features   : SSC group table + SQI group table (+ not-assessable row styling)
   ├─ PSQI       : component bars + global score (or "Not taken")
   └─ Report     : markdown render + [Generate] button + generated_at/model info
```

**Status polling:** after upload, poll `/studies/{id}/` every 4 s. Show
`status_message`; on `failed` show `error_message` (e.g. "No frontal EEG
channel found…") with a retry (re-upload) action.

**Review workflow (assistant-to-expert):** on the Staging tab, render epochs
with `needs_review = true` in a warning color; the Overview banner shows
`needs_review_pct`; clicking a flagged epoch jumps to Signals and zooms to it.

---

## 7. Charts cookbook

**Hypnogram** (`/ssc/`): use `frames.stage` with fixed display order
`[Wake, REM, N1, N2, N3]` on the y-axis (Wake at top). E.g. map code → y:
`{0:0, 4:1, 1:2, 2:3, 3:4}`; x = `start_sec / 3600` for hours.

**Confidence ribbon:** second row under the hypnogram; per epoch a thin rect
colored by `confidence_band` (green / amber / red), tooltip = confidence +
full 5-element `probabilities`. Vertical lines at `confidence_bands.high`
(0.80) for reference if you show a confidence line chart.

**Depth curve** (`/sdi/`): line of `frames.sdi` (0–1); shade or mark
`frames.rem_pred == 1` windows; dashed guides at 0.2 (shallow) and 0.8 (deep);
annotate `substitutions` (e.g. "ECG zero-filled — exploratory") and the
`caveat`.

**Stage distribution:** donut from `night.stage_pct` (whole recording) or from
sleep-time shares `n*_pct_tst` in `features/ssc` (of TST) — label which
denominator you use.

**Signals overview** (`/signals/`): for each channel draw the min/max envelope
(area between min and max along t). Use a canvas-based chart (uPlot, Plotly,
Chart.js) — 1200 points × ≤8 channels renders instantly. Click → compute
`epoch = floor(t/30)` → open `/signals/{epoch}/` (fetch the same channels).

**Features tables:** two columns — value + label. Render `null` as "—" and
**never** render a missing key as 0; if the key is in `not_assessable`, show
the value cell as "Not assessable" with the reason as a tooltip. For SQI
features show orientation chips (↓ better for `sdi_rb`, `sdi_cv`; ↑ better for
`sdi_ap`, `sdi_mdr`, `sdi_pr`).

**Reference hints** (for value coloring/interpretation):
SE ≥ 85% · SOL ≤ 30 min · REM latency 60–120 min · N3 10–25% of TST ·
REM 18–25% of TST · arousal index ≤ 25/h (proxy!) · spindle density ≈ 1–3/min.
Show these as "typical adult" captions, not as hard pass/fail gates.

---

## 8. Formatting & honesty rules (important)

1. **Confidence = probability, not a verdict.** Always show class + confidence
   (e.g. "REM · 0.4" vs "REM · 0.8"). Use bands: high (≥0.80) confident;
   medium (0.60–0.80) review recommended; low (<0.60) suspicious.
2. **Never fabricate a value.** Missing / `not_assessable` items display as
   "Not assessable" + the provided reason — never as `0`. A zero apnea count
   from a 1-Hz envelope would falsely read as "healthy".
3. **Label SDI as exploratory.** Show the `caveat` and the `substitutions`
   flags wherever depth numbers appear (depth is zero-shot with ECG zero-filled
   and cassette EMG upsampled).
4. **Percentages need denominators.** `stage_pct` is of the whole recording
   (includes Wake); `n*_pct_tst` is of total sleep time. Label accordingly.
5. **Time formats.** `start_sec` is seconds from recording start; format as
   `HH:MM` offsets (e.g. `2:23:30`) or clock time if you also read
   `signal_quality`/night start — do not invent clock times if absent.
6. **The report is decision support, not diagnosis** — keep its closing
   disclaimer visible.

---

## 9. Limits, gotchas, performance

| Item | Limit / behaviour |
|---|---|
| Upload file | `.edf`, ≤ 500 MB; `POST /studies/` may block ~2 min in dev (eager Celery) → client timeout ≥ 180 s, or switch the backend to Redis+Celery for instant return |
| Processing | ~90–120 s per night (CPU) |
| Signal preview | ≤ 8 channels/request, `duration_sec` ≤ 3600, `max_points` ≤ 4000 |
| Epoch snippet | `points` ≤ 3000 (default 750), `epoch_index` from the same 30-s grid |
| Throttles | register 3/h · login 10/min · uploads 20/h · report generation 10/h → handle 429 politely |
| List size | default `limit=20`, max 100 — always paginate |
| Report generation | 8–20 s → disable the button while pending; 503 = server has no LLM key |
| 401 mid-session | refresh once, retry; on failure redirect to login |
| Cookies in dev | `SESSION_COOKIE_SECURE=False` (http works); use `credentials: "include"` and ensure the backend `CORS_ALLOWED_ORIGINS` contains your dev origin |

---

## 10. Suggested libraries

- **Data fetching:** TanStack Query (polling, caching) + the `api()` wrapper above
- **Charts:** uPlot (fast canvas, best for signals) or Plotly; Chart.js for donut/bars
- **Markdown:** `react-markdown` + `remark-gfm`
- **Forms:** react-hook-form + zod (mirror the envelope errors into field errors)
- **Upload:** plain `FormData` + progress events (XHR or fetch + streams)
- **Styling:** Tailwind is already scaffolded in `frontend/`

---

## 11. Acceptance checklist

- [ ] Register → login → `me` works; refresh keeps the session alive; logout clears cookies
- [ ] Upload a `.edf` (with/without patient, with/without complete PSQI) → 201
- [ ] Partial PSQI is impossible in the UI (all-or-nothing) and rejected server-side
- [ ] Study list: search, status, date range, ordering, pagination all functional
- [ ] Polling shows `processing → completed`; failures show `error_message`
- [ ] Hypnogram + confidence ribbon render from `/ssc/`; flagged epochs clickable
- [ ] Depth curve renders from `/sdi/` with REM markers + caveat/substitutions visible
- [ ] Signals overview renders min/max envelopes; clicking zooms to `/signals/{epoch}/`
- [ ] Download button fetches `/download/`
- [ ] Features screens split SSC vs SQI; `not_assessable` items show reasons, never 0
- [ ] PSQI card supports view / edit / delete (Pittsburgh components, 0–3)
- [ ] Patients: create · search · update · delete (studies survive unlinked) · patient studies list
- [ ] Report tab: generate (spinner), render markdown, show model + generated_at
- [ ] Assistant tab: session + history render; send message; `503 OPENCODE_UNAVAILABLE` shows a clear message; suggested-prompt chips clickable
- [ ] 401/429/503 handled with human messages
