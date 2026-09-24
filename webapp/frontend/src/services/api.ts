import axios from 'axios';
import type {
  ApiResponse,
  Patient,
  SleepStudy,
  StudyFile,
  SleepEpoch,
  MetricDefinition,
  StudyMetricsSummary,
  ClinicalReport,
  ChatSession,
  ChatMessage,
  StudyStatus
} from '../types';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  withCredentials: true,
});

export const api = {
  // --- Patients ---
  async getPatients(): Promise<Patient[]> {
    const res = await apiClient.get<ApiResponse<Patient[]>>('/patients/');
    return res.data.data;
  },

  async createPatient(patientData: {
    mrn: string;
    first_name: string;
    last_name: string;
    birth_date?: string | null;
    biological_sex: string;
    medical_history?: string;
  }): Promise<Patient> {
    const res = await apiClient.post<ApiResponse<Patient>>('/patients/', patientData);
    return res.data.data;
  },

  // --- Studies ---
  async getStudies(): Promise<SleepStudy[]> {
    const res = await apiClient.get<ApiResponse<SleepStudy[]>>('/studies/');
    return res.data.data;
  },

  async getStudyDetail(studyId: string): Promise<SleepStudy> {
    const res = await apiClient.get<ApiResponse<SleepStudy>>(`/studies/${studyId}/`);
    return res.data.data;
  },

  async uploadStudy(formData: FormData): Promise<{ study_id: string; status: StudyStatus }> {
    const res = await apiClient.post<ApiResponse<{ study_id: string; status: StudyStatus }>>(
      '/studies/upload/',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return res.data.data;
  },

  async getStudyStatus(studyId: string): Promise<{
    study_id: string;
    status: StudyStatus;
    status_display: string;
    total_epochs: number;
    duration_minutes: number;
    error_log: string;
  }> {
    const res = await apiClient.get<ApiResponse<{
      study_id: string;
      status: StudyStatus;
      status_display: string;
      total_epochs: number;
      duration_minutes: number;
      error_log: string;
    }>>(`/studies/${studyId}/status/`);
    return res.data.data;
  },

  async getStudyFiles(studyId: string, fileType?: string): Promise<StudyFile[]> {
    const url = fileType ? `/studies/${studyId}/files/?file_type=${fileType}` : `/studies/${studyId}/files/`;
    const res = await apiClient.get<ApiResponse<StudyFile[]>>(url);
    return res.data.data;
  },

  // --- Hypnograms & Staging ---
  async getStudyHypnogram(studyId: string): Promise<SleepEpoch[]> {
    const res = await apiClient.get<ApiResponse<SleepEpoch[]>>(`/studies/${studyId}/hypnogram/`);
    return res.data.data;
  },

  async overrideEpoch(
    studyId: string,
    epochIndex: number,
    stage: number,
    reason: string
  ): Promise<SleepEpoch> {
    const res = await apiClient.patch<ApiResponse<SleepEpoch>>(
      `/studies/${studyId}/epochs/${epochIndex}/override/`,
      { stage, correction_reason: reason }
    );
    return res.data.data;
  },

  async bulkOverrideEpochs(
    studyId: string,
    startEpoch: number,
    endEpoch: number,
    stage: number,
    reason: string
  ): Promise<{ updated_epochs_count: number; stage: number }> {
    const res = await apiClient.post<ApiResponse<{ updated_epochs_count: number; stage: number }>>(
      `/studies/${studyId}/epochs/bulk-override/`,
      { start_epoch: startEpoch, end_epoch: endEpoch, stage, correction_reason: reason }
    );
    return res.data.data;
  },

  // --- Metrics ---
  async getStudyMetrics(studyId: string): Promise<StudyMetricsSummary> {
    const res = await apiClient.get<ApiResponse<StudyMetricsSummary>>(`/studies/${studyId}/metrics/`);
    return res.data.data;
  },

  async overrideMetric(
    studyId: string,
    metricKey: string,
    adjustedValue: number,
    rationale: string
  ): Promise<StudyMetricsSummary> {
    const res = await apiClient.post<ApiResponse<StudyMetricsSummary>>(
      `/studies/${studyId}/metrics/override/`,
      { metric_key: metricKey, adjusted_value: adjustedValue, clinical_rationale: rationale }
    );
    return res.data.data;
  },

  async recalculateMetrics(studyId: string): Promise<StudyMetricsSummary> {
    const res = await apiClient.post<ApiResponse<StudyMetricsSummary>>(`/studies/${studyId}/metrics/recalculate/`);
    return res.data.data;
  },

  async getMetricsCatalog(): Promise<MetricDefinition[]> {
    const res = await apiClient.get<ApiResponse<MetricDefinition[]>>('/metrics/catalog/');
    return res.data.data;
  },

  // --- Clinical Reports ---
  async getClinicalReport(studyId: string): Promise<ClinicalReport> {
    const res = await apiClient.get<ApiResponse<ClinicalReport>>(`/studies/${studyId}/report/`);
    return res.data.data;
  },

  async signOffReport(studyId: string, isSignedOff: boolean, physicianNotes: string): Promise<ClinicalReport> {
    const res = await apiClient.post<ApiResponse<ClinicalReport>>(`/studies/${studyId}/report/sign-off/`, {
      is_signed_off: isSignedOff,
      physician_notes: physicianNotes,
    });
    return res.data.data;
  },

  async regenerateReport(studyId: string): Promise<ClinicalReport> {
    const res = await apiClient.post<ApiResponse<ClinicalReport>>(`/studies/${studyId}/report/regenerate/`);
    return res.data.data;
  },

  // --- Doctor-LLM Assistant Chat ---
  async getOrCreateChatSession(studyId: string): Promise<ChatSession> {
    const res = await apiClient.post<ApiResponse<ChatSession>>(`/studies/${studyId}/chat/`);
    return res.data.data;
  },

  async getChatMessages(studyId: string, sessionId: string): Promise<ChatMessage[]> {
    const res = await apiClient.get<ApiResponse<ChatMessage[]>>(`/studies/${studyId}/chat/${sessionId}/messages/`);
    return res.data.data;
  },

  async sendChatMessage(studyId: string, sessionId: string, content: string): Promise<ChatMessage> {
    const res = await apiClient.post<ApiResponse<ChatMessage>>(`/studies/${studyId}/chat/${sessionId}/message/`, {
      content,
    });
    return res.data.data;
  },

  async getSuggestedPrompts(studyId: string, sessionId: string): Promise<string[]> {
    const res = await apiClient.get<ApiResponse<string[]>>(`/studies/${studyId}/chat/${sessionId}/suggested-prompts/`);
    return res.data.data;
  },

  // --- SSE Real-Time Token Streaming ---
  streamChatMessage(
    studyId: string,
    sessionId: string,
    prompt: string,
    onToken: (token: string) => void,
    onComplete: () => void,
    onError: (err: Error) => void
  ): () => void {
    const encodedPrompt = encodeURIComponent(prompt);
    const url = `/api/v1/studies/${studyId}/chat/${sessionId}/stream/?prompt=${encodedPrompt}`;

    const controller = new AbortController();

    fetch(url, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok || !response.body) {
          throw new Error(`SSE request failed with status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const parsed = JSON.parse(line.slice(6)) as { delta?: string; done?: boolean };
                if (parsed.delta) {
                  onToken(parsed.delta);
                }
                if (parsed.done) {
                  onComplete();
                  return;
                }
              } catch {
                // Ignore partial JSON
              }
            }
          }
        }
        onComplete();
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          onError(err instanceof Error ? err : new Error(String(err)));
        }
      });

    return () => controller.abort();
  }
};
