"use client";

/**
 * useStudyReport Hook
 * Loads every payload of a completed study and normalizes the epoch stream.
 */

import { useMemo } from "react";
import {
  useFeaturesQuery,
  useNightQuery,
  usePsqiQuery,
  useReportQuery,
  useSdiQuery,
  useSscQuery,
  useStudyQuery,
} from "@/lib/api/queries";
import type { EpochDatum, UseReportReturn } from "../types";

export function useStudyReport(studyId: string): UseReportReturn {
  const studyQuery = useStudyQuery(studyId, true);
  const study = studyQuery.data ?? null;
  const isAnalyzing =
    study?.status === "processing" || study?.status === "uploaded" || false;
  const isFailed = study?.status === "failed" || false;

  const nightQuery = useNightQuery(studyId, isAnalyzing || Boolean(study));
  const sscQuery = useSscQuery(studyId, Boolean(study));
  const sdiQuery = useSdiQuery(studyId, Boolean(study));
  const featuresQuery = useFeaturesQuery(studyId, Boolean(study));
  const psqiQuery = usePsqiQuery(studyId, Boolean(study));
  const reportQuery = useReportQuery(studyId, Boolean(study));

  const epochs = useMemo<EpochDatum[]>(() => {
    const ssc = sscQuery.data;
    const sdi = sdiQuery.data;
    if (!ssc?.frames) return [];
    const sdiMap = new Map<number, { sdi: number | null; rem: boolean | null }>();
    if (sdi?.frames) {
      sdi.frames.index.forEach((index, position) => {
        const rawRem = sdi.frames.rem_pred[position];
        sdiMap.set(index, { sdi: sdi.frames.sdi[position], rem: rawRem === null ? null : Boolean(rawRem) });
      });
    }
    return ssc.frames.index.map((index, position) => ({
      index,
      startSec: ssc.frames.start_sec[position],
      stageCode: ssc.frames.stage[position],
      stage: (ssc.stage_labels[ssc.frames.stage[position]] as EpochDatum["stage"]) ?? null,
      confidence: ssc.frames.confidence[position],
      band: ssc.frames.confidence_band[position],
      needsReview: ssc.frames.needs_review[position],
      probabilities: ssc.frames.probabilities[position],
      sdi: sdiMap.get(index)?.sdi ?? null,
      remPred: sdiMap.get(index)?.rem ?? null,
    }));
  }, [sscQuery.data, sdiQuery.data]);

  return {
    data: {
      study,
      night: nightQuery.data ?? null,
      ssc: sscQuery.data ?? null,
      sdi: sdiQuery.data ?? null,
      features: featuresQuery.data ?? null,
      psqi: psqiQuery.data ?? null,
      report: reportQuery.data ?? null,
    },
    epochs,
    isAnalyzing,
    isFailed,
    isLoading:
      studyQuery.isLoading ||
      (Boolean(study) &&
        (sscQuery.isLoading || sdiQuery.isLoading || featuresQuery.isLoading)),
  };
}
