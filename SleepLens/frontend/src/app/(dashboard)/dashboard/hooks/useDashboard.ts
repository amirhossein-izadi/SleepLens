"use client";

/**
 * useDashboard Hook
 * Aggregates study list data into dashboard KPIs and recent studies.
 */

import { useMemo } from "react";
import { useStudiesQuery } from "@/lib/api/queries";
import type { Study } from "@/lib/api";

export interface DashboardStats {
  total: number;
  completed: number;
  processing: number;
  failed: number;
  avgSleepPct: number | null;
  avgConfidence: number | null;
}

export interface UseDashboardReturn {
  stats: DashboardStats;
  recent: Study[];
  isLoading: boolean;
  processingPoll: boolean;
}

export function useDashboard(): UseDashboardReturn {
  const { data, isLoading } = useStudiesQuery(undefined, true);

  const stats = useMemo<DashboardStats>(() => {
    const studies = data?.results ?? [];
    const completed = studies.filter((study) => study.status === "completed");
    const sleepValues = completed
      .map((study) => study.summary?.sleep_pct)
      .filter((value): value is number => typeof value === "number");
    const confidenceValues = completed
      .map((study) => study.summary?.mean_confidence)
      .filter((value): value is number => typeof value === "number");
    return {
      total: data?.total ?? 0,
      completed: completed.length,
      processing: studies.filter((study) => study.status === "processing").length,
      failed: studies.filter((study) => study.status === "failed").length,
      avgSleepPct: sleepValues.length
        ? sleepValues.reduce((sum, value) => sum + value, 0) / sleepValues.length
        : null,
      avgConfidence: confidenceValues.length
        ? confidenceValues.reduce((sum, value) => sum + value, 0) / confidenceValues.length
        : null,
    };
  }, [data]);

  const recent = useMemo(() => (data?.results ?? []).slice(0, 5), [data]);

  return {
    stats,
    recent,
    isLoading,
    processingPoll: stats.processing > 0,
  };
}
