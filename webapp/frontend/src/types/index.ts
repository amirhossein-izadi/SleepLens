export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  message?: string | null;
  metadata?: Record<string, unknown>;
  error?: {
    code: string;
    message: string;
    details?: unknown[];
  };
}

export type BiologicalSex = 'male' | 'female' | 'other';

export interface Patient {
  id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  birth_date?: string | null;
  biological_sex: BiologicalSex;
  biological_sex_display?: string;
  medical_history?: string;
  created_at: string;
  updated_at?: string;
}

export type StudyStatus = 
  | 'uploaded'
  | 'extracting'
  | 'staging'
  | 'computing_metrics'
  | 'generating_report'
  | 'completed'
  | 'failed';

export type StudyType = 'cassette_home' | 'telemetry_hospital' | 'full_psg';

export interface SleepStudy {
  id: string;
  patient: Patient;
  study_date: string;
  study_type: StudyType;
  status: StudyStatus;
  raw_archive?: string | null;
  extracted_path?: string;
  total_epochs: number;
  duration_minutes: number;
  sqi_score?: number | null;
  sqi_category?: string | null;
  metadata?: Record<string, unknown>;
  error_log?: string;
  created_at: string;
  updated_at?: string;
}

export interface StudyFile {
  id: string;
  study_id: string;
  file_name: string;
  relative_path: string;
  file_type: string;
  file_type_display: string;
  file_size_bytes: number;
  file_hash_sha256: string;
  epoch_index?: number | null;
  preview_data?: Record<string, unknown>;
  created_at: string;
}

export interface SleepEpoch {
  id: string;
  epoch_index: number;
  start_seconds: number;
  stage: number; // 0=Wake, 1=N1, 2=N2, 3=N3, 4=REM, -1=Unscored
  stage_display: string;
  ai_predicted_stage: number;
  ai_predicted_stage_display: string;
  confidence: number;
  is_manually_corrected: boolean;
  correction_reason?: string;
  is_lights_off: boolean;
  metrics?: Record<string, unknown>;
}

export interface MetricDefinition {
  key: string;
  display_name: string;
  category: string;
  category_display: string;
  unit: string;
  normal_min?: number | null;
  normal_max?: number | null;
  description?: string;
  is_editable: boolean;
  show_in_report: boolean;
  display_order: number;
}

export interface StudyMetricsSummary {
  id: string;
  study_id: string;
  sqi_score: number;
  sqi_category: string;
  metrics_data: Record<string, number>;
  ai_raw_metrics: Record<string, number>;
  category_summaries: Record<string, { score: number; status: string }>;
  overrides?: Record<string, unknown>;
  is_manually_adjusted: boolean;
  clinical_alerts: string[];
  is_valid: boolean;
  computed_at: string;
  updated_at: string;
}

export interface ClinicalReport {
  id: string;
  study_id: string;
  llm_model_name: string;
  executive_summary: string;
  architecture_findings: string;
  respiratory_and_micro_notes: string;
  differential_diagnoses: string[];
  clinical_recommendations: string[];
  physician_notes?: string;
  is_signed_off: boolean;
  signed_off_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  sender: 'physician' | 'assistant' | 'system';
  sender_display?: string;
  content: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  created_at: string;
}

export interface ChatSession {
  id: string;
  study_id: string;
  physician_id?: number | null;
  opencode_session_id?: string;
  title: string;
  created_at: string;
  updated_at?: string;
  messages?: ChatMessage[];
}
