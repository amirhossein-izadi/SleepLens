import { STAGES } from "@/lib/format";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  date_joined?: string;
}

export interface Patient {
  id: string;
  full_name: string;
  sex?: string;
  birth_year?: number | null;
}

export interface AnalysisWindow {
  start_epoch: number;
  end_epoch: number;
  start_sec: number;
  end_sec: number;
  n_epochs?: number;
}

export interface SdiMetrics {
  rb?: number | null;
  ap?: number | null;
  cv?: number | null;
  mdr?: number | null;
  pr?: number | null;
}

/** SQI model composite (from the SDI pipeline; percentile vs Sleep-EDF reference). */
export interface SdiComposite {
  components: Record<string, number>;
  composite: number;
  percentile: number;
  reference?: string;
  note?: string;
}

export interface SignalQuality {
  channels?: Record<string, string>;
  sample_rates?: Record<string, number>;
  substitutions?: Record<string, boolean>;
  analysis_window?: AnalysisWindow;
  n_epochs_total?: number;
  sleep_epochs?: number;
}

export type StudyStatus = "uploaded" | "processing" | "completed" | "failed";

export interface Study {
  id: string;
  original_filename: string;
  file_size: number;
  download_url: string;
  status: StudyStatus;
  status_message: string | null;
  error_message: string | null;
  patient: Patient | null;
  duration_minutes: number | null;
  n_epochs: number | null;
  summary: NightSummaryShape | null;
  signal_quality: SignalQuality | null;
  psqi_taken: boolean;
  psqi_global_score: number | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

/** study.summary nested shape (built by the pipeline). */
export interface NightSummaryShape {
  stage_counts?: Record<string, number>;
  stage_pct?: Record<string, number>;
  sleep_pct?: number;
  mean_confidence?: number;
  needs_review_count?: number;
  needs_review_pct?: number;
  sdi_metrics?: SdiMetrics;
  sdi_composite?: SdiComposite | null;
  staging_system?: string;
  staging_members?: string[];
  analysis_window?: AnalysisWindow;
  [key: string]: unknown;
}

/** The axios envelope interceptor turns paginated lists into rows + metadata.total. */
export interface StudyList<T> {
  results: T[];
  total: number;
}

export interface NightPayload {
  study_id: string;
  original_filename: string;
  status: StudyStatus;
  status_message: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  duration_minutes: number | null;
  n_epochs: number | null;
  staging_system: string | null;
  staging_members: string[] | null;
  analysis_window: AnalysisWindow | null;
  stage_counts: Record<string, number> | null;
  stage_pct: Record<string, number> | null;
  sleep_pct: number | null;
  mean_confidence: number | null;
  needs_review_count: number | null;
  needs_review_pct: number | null;
  sdi_metrics: SdiMetrics | null;
  sdi_composite: SdiComposite | null;
  signal_quality: SignalQuality | null;
}

export interface HypnogramFeature {
  sol_min?: number | null;
  waso_min?: number | null;
  rem_lat_min?: number | null;
  n_awakenings?: number;
  awakening_index?: number | null;
  n_stage_shifts?: number;
  shift_index?: number | null;
  sfi?: number | null;
  n_rem_episodes?: number;
  mean_rem_bout_min?: number | null;
  longest_sleep_bout_min?: number | null;
  mean_sleep_bout_min?: number | null;
  longest_wake_post_onset_min?: number | null;
  transitions?: Record<string, number>;
  [key: string]: unknown;
}

export interface SscFeatures {
  eeg_epochs_analyzed?: number;
  [key: string]: unknown;
}

export interface SqiFeatures {
  sdi_rb?: number | null;
  sdi_ap?: number | null;
  sdi_cv?: number | null;
  sdi_skew?: number | null;
  sdi_mdr?: number | null;
  sdi_pr?: number | null;
  sdi_mean_sleep?: number | null;
  sdi_std_sleep?: number | null;
  sdi_p05?: number | null;
  sdi_p95?: number | null;
  sdi_shallow_minutes?: number | null;
  sdi_deep_minutes?: number | null;
  sdi_auc?: number | null;
  sdi_apen?: number | null;
  sdi_dfa?: number | null;
  [key: string]: unknown;
}

export interface NotAssessableEntry {
  key: string;
  reason: string;
}

export interface FeaturesPayload {
  study_id: string;
  available: boolean;
  values: { ssc: Record<string, unknown>; sqi: Record<string, unknown> };
  not_assessable: NotAssessableEntry[];
}

export interface SscPayload {
  study_id: string;
  n_epochs: number;
  epoch_seconds: number;
  stage_codes: Record<string, number>;
  stage_labels: string[];
  confidence_bands: { high: number; medium: number };
  frames: {
    index: number[];
    start_sec: number[];
    stage: number[];
    probabilities: number[][];
    confidence: number[];
    confidence_band: ("high" | "medium" | "low")[];
    needs_review: boolean[];
  };
  stage_summary: Record<
    string,
    { count: number; pct: number; mean_confidence: number | null; review_count: number }
  >;
  review_summary: {
    needs_review_count: number;
    needs_review_pct: number;
    low_confidence_count: number;
    low_confidence_pct: number;
  };
}

export interface SdiPayload {
  study_id: string;
  model: string;
  n_epochs: number;
  epoch_seconds: number;
  sdi_range: [number, number];
  sdi_note: string;
  frames: {
    index: number[];
    start_sec: number[];
    sdi: (number | null)[];
    rem_pred: (number | null)[];
  };
  sdi_stats: { n: number; mean: number | null; min: number | null; max: number | null };
  substitutions: Record<string, boolean>;
}

export interface ReportPayload {
  study_id: string;
  available: boolean;
  markdown: string | null;
  model_name?: string;
  prompt_version?: string;
  generated_at?: string;
}

export interface PsqiPayload {
  taken: boolean;
  global_score: number | null;
  components: Record<string, number>;
}

export interface StudyListFilters {
  search?: string;
  status?: StudyStatus | "";
}

/** Stage helper for typed access. */
export const stageLabels = STAGES;
