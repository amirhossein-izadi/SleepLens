"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authApi, studiesApi } from "@/lib/api";
import type { StudyListFilters, StudyStatus } from "@/lib/api/types";
import { useAuthStore } from "@/lib/store";
import { extractErrorMessage } from "@/lib/errorUtils";

/** ── Query keys ─────────────────────────────────────────────────────────── */

export const queryKeys = {
  auth: {
    me: () => ["auth", "me"] as const,
  },
  studies: {
    root: ["studies"] as const,
    list: (filters?: StudyListFilters) => ["studies", "list", filters ?? {}] as const,
    detail: (id: string) => ["studies", "detail", id] as const,
    night: (id: string) => ["studies", "night", id] as const,
    ssc: (id: string) => ["studies", "ssc", id] as const,
    sdi: (id: string) => ["studies", "sdi", id] as const,
    features: (id: string) => ["studies", "features", id] as const,
    psqi: (id: string) => ["studies", "psqi", id] as const,
    report: (id: string) => ["studies", "report", id] as const,
    signals: (id: string, startSec: number, durationSec: number, channels?: string) =>
      ["studies", "signals", id, channels ?? "default", startSec, durationSec] as const,
    epoch: (id: string, epochIndex: number, channels?: string) =>
      ["studies", "epoch", id, channels ?? "default", epochIndex] as const,
    assistant: (id: string) => ["studies", "assistant", id] as const,
  },
};

/** ── Auth ───────────────────────────────────────────────────────────────── */

export function useMeQuery(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: authApi.me,
    retry: false,
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

/** ── Studies ────────────────────────────────────────────────────────────── */

export function useStudiesQuery(filters?: StudyListFilters, poll = false) {
  return useQuery({
    queryKey: queryKeys.studies.list(filters),
    queryFn: () => studiesApi.list(filters),
    refetchInterval: poll ? 5000 : false,
  });
}

export function useStudyQuery(id: string, poll = false) {
  return useQuery({
    queryKey: queryKeys.studies.detail(id),
    queryFn: () => studiesApi.get(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status as StudyStatus | undefined;
      return status === "processing" || status === "uploaded" ? 5000 : false;
    },
    refetchIntervalInBackground: false,
    enabled: Boolean(id),
  });
}

export function useNightQuery(id: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.studies.night(id),
    queryFn: () => studiesApi.night(id),
    enabled,
  });
}

export function useSscQuery(id: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.studies.ssc(id),
    queryFn: () => studiesApi.ssc(id),
    enabled,
  });
}

export function useSdiQuery(id: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.studies.sdi(id),
    queryFn: () => studiesApi.sdi(id),
    enabled,
  });
}

export function useFeaturesQuery(id: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.studies.features(id),
    queryFn: () => studiesApi.features(id),
    enabled,
  });
}

export function usePsqiQuery(id: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.studies.psqi(id),
    queryFn: () => studiesApi.psqi(id),
    enabled,
  });
}

export function useReportQuery(id: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.studies.report(id),
    queryFn: () => studiesApi.report(id),
    enabled,
  });
}

export function useSignalsQuery(
  id: string,
  options: { start_sec: number; duration_sec: number; channels?: string; enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.studies.signals(
      id,
      options.start_sec,
      options.duration_sec,
      options.channels
    ),
    queryFn: () =>
      studiesApi.signals(id, {
        start_sec: options.start_sec,
        duration_sec: options.duration_sec,
        channels: options.channels,
      }),
    enabled: options.enabled ?? Boolean(id),
  });
}

export function useEpochQuery(
  id: string,
  epochIndex: number,
  channels?: string,
  enabled = true
) {
  return useQuery({
    queryKey: queryKeys.studies.epoch(id, epochIndex, channels),
    queryFn: () => studiesApi.signalEpoch(id, epochIndex, { channels }),
    enabled,
  });
}

export function useGenerateReportMutation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => studiesApi.generateReport(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.studies.report(id) });
    },
  });
}

export function useReprocessMutation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => studiesApi.reprocess(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.studies.root });
    },
  });
}

/** ── Assistant (opencode-backed consultation, docs §4.4) ────────────────── */

export function useAssistantQuery(studyId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.studies.assistant(studyId),
    queryFn: () => studiesApi.assistant(studyId),
    enabled,
    staleTime: 30 * 1000,
  });
}

export function useAssistantPromptsQuery(studyId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["studies", "assistant-prompts", studyId] as const,
    queryFn: () => studiesApi.assistantPrompts(studyId),
    enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useAssistantStartMutation(studyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => studiesApi.assistantCreate(studyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.studies.assistant(studyId) });
    },
  });
}

export function useAssistantSendMutation(studyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => studiesApi.assistantSend(studyId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.studies.assistant(studyId) });
    },
  });
}

export function useAssistantResetMutation(studyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => studiesApi.assistantReset(studyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.studies.assistant(studyId) });
    },
  });
}

export function useDeleteStudyMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => studiesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.studies.root });
    },
  });
}

export function useUploadMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      file,
      patientId,
      psqi,
    }: {
      file: File;
      patientId?: string;
      psqi?: Record<string, number>;
    }) => studiesApi.create(file, { patientId, psqi }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.studies.root });
    },
  });
}

export function useAuthError(err: unknown, fallback: string): string {
  return extractErrorMessage(err, fallback);
}
