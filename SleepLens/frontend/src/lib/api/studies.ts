import { api } from "./base";
import type {
  FeaturesPayload,
  NightPayload,
  PsqiPayload,
  ReportPayload,
  SdiPayload,
  SscPayload,
  Study,
  StudyList,
  StudyListFilters,
  StudyStatus,
} from "./types";
import type { SignalsPreview as SignalsPayload } from "./signalTypes";
import type { AssistantPayload, AssistantSendResult } from "./assistant";

export const studiesApi = {
  list: async (filters?: StudyListFilters): Promise<StudyList<Study>> => {
    const params = new URLSearchParams();
    if (filters?.search) params.append("search", filters.search);
    if (filters?.status) params.append("status", filters.status);
    const qs = params.toString();
    const response = await api.get<Study[]>(`/studies/${qs ? `?${qs}` : ""}`);
    return {
      results: response.data,
      total: response.metadata?.total ?? response.data.length,
    };
  },

  get: async (id: string): Promise<Study> => {
    const response = await api.get<Study>(`/studies/${id}/`);
    return response.data;
  },

  create: async (file: File, options?: { patientId?: string; psqi?: Record<string, number> }): Promise<Study> => {
    const form = new FormData();
    form.append("file", file);
    if (options?.patientId) form.append("patient", options.patientId);
    if (options?.psqi) form.append("psqi", JSON.stringify(options.psqi));
    // Dev config runs Celery eagerly: the request can block ~2 min while the
    // night is analyzed — keep a generous timeout.
    const response = await api.post<Study>("/studies/", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 180_000,
    });
    return response.data;
  },

  night: async (id: string): Promise<NightPayload> => {
    const response = await api.get<NightPayload>(`/studies/${id}/night/`);
    return response.data;
  },

  ssc: async (id: string): Promise<SscPayload> => {
    const response = await api.get<SscPayload>(`/studies/${id}/ssc/`);
    return response.data;
  },

  sdi: async (id: string): Promise<SdiPayload> => {
    const response = await api.get<SdiPayload>(`/studies/${id}/sdi/`);
    return response.data;
  },

  features: async (id: string): Promise<FeaturesPayload> => {
    const response = await api.get<FeaturesPayload>(`/studies/${id}/features/`);
    return response.data;
  },

  psqi: async (id: string): Promise<PsqiPayload> => {
    const response = await api.get<PsqiPayload>(`/studies/${id}/psqi/`);
    return response.data;
  },

  report: async (id: string): Promise<ReportPayload> => {
    const response = await api.get<ReportPayload>(`/studies/${id}/report/`);
    return response.data;
  },

  generateReport: async (id: string): Promise<ReportPayload> => {
    const response = await api.post<ReportPayload>(`/studies/${id}/report/generate/`);
    return response.data;
  },

  signals: async (
    id: string,
    options?: { channels?: string; start_sec?: number; duration_sec?: number; max_points?: number }
  ): Promise<SignalsPayload> => {
    const params = new URLSearchParams();
    if (options?.channels) params.append("channels", options.channels);
    if (options?.start_sec !== undefined) params.append("start_sec", String(options.start_sec));
    if (options?.duration_sec !== undefined)
      params.append("duration_sec", String(options.duration_sec));
    if (options?.max_points !== undefined) params.append("max_points", String(options.max_points));
    const response = await api.get<SignalsPayload>(`/studies/${id}/signals/?${params.toString()}`);
    return response.data;
  },

  signalEpoch: async (
    id: string,
    epochIndex: number,
    options?: { channels?: string; points?: number }
  ): Promise<SignalsPayload> => {
    const params = new URLSearchParams();
    if (options?.channels) params.append("channels", options.channels);
    if (options?.points) params.append("points", String(options.points));
    const response = await api.get<SignalsPayload>(
      `/studies/${id}/signals/${epochIndex}/?${params.toString()}`
    );
    return response.data;
  },

  reprocess: async (id: string): Promise<Study> => {
    const response = await api.post<Study>(`/studies/${id}/reprocess/`);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/studies/${id}/`);
  },

  // ── Assistant consultation (opencode-backed; docs §4.4) ───────────────────
  //   GET    /studies/{id}/chat/                  → session + full history
  //   POST   /studies/{id}/chat/                  → create/re-fetch session
  //   DELETE /studies/{id}/chat/                  → reset consultation
  //   POST   /studies/{id}/chat/messages/         → {content} → assistant reply
  //   GET    /studies/{id}/chat/suggested-prompts → question chips

  assistant: async (id: string): Promise<AssistantPayload> => {
    const response = await api.get<AssistantPayload>(`/studies/${id}/chat/`);
    return response.data;
  },

  assistantCreate: async (id: string): Promise<AssistantPayload> => {
    const response = await api.post<AssistantPayload>(`/studies/${id}/chat/`);
    return response.data;
  },

  assistantReset: async (id: string): Promise<void> => {
    await api.delete(`/studies/${id}/chat/`);
  },

  assistantSend: async (id: string, content: string): Promise<AssistantSendResult> => {
    const response = await api.post<AssistantSendResult>(`/studies/${id}/chat/messages/`, {
      content,
    });
    return response.data;
  },

  assistantPrompts: async (id: string): Promise<string[]> => {
    const response = await api.get<unknown>(`/studies/${id}/chat/suggested-prompts/`);
    const data = response.data;
    if (Array.isArray(data)) return data as string[];
    if (data && typeof data === "object") {
      const record = data as { prompts?: string[]; suggested_prompts?: string[] };
      return record.prompts ?? record.suggested_prompts ?? [];
    }
    return [];
  },
};

export type { StudyStatus };
