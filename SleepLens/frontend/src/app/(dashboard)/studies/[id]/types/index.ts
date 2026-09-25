/**
 * Report page types + derivations shared by all report components.
 */

import type {
  FeaturesPayload,
  NightPayload,
  NotAssessableEntry,
  PsqiPayload,
  ReportPayload,
  SdiPayload,
  SscPayload,
  Study,
} from "@/lib/api";
import type { Stage } from "@/lib/format";

export type { Stage };

/** Everything the report page needs, keyed by concern. */
export interface ReportData {
  study: Study | null;
  night: NightPayload | null;
  ssc: SscPayload | null;
  sdi: SdiPayload | null;
  features: FeaturesPayload | null;
  psqi: PsqiPayload | null;
  report: ReportPayload | null;
}

export interface EpochDatum {
  index: number;
  startSec: number;
  stage: Stage | null;
  stageCode: number;
  confidence: number;
  band: "high" | "medium" | "low";
  needsReview: boolean;
  probabilities: number[];
  sdi: number | null;
  remPred: boolean | null;
}

export interface UseReportReturn {
  data: ReportData | null;
  epochs: EpochDatum[];
  isAnalyzing: boolean;
  isFailed: boolean;
  isLoading: boolean;
}

export const SECONDS_PER_EPOCH = 30;

export const SQI_FEATURE_META: Record<string, { label: string; hint: string; unit?: string }> = {
  sdi_rb: {
    label: "Shallow burden",
    hint: "Fraction of sleep epochs below the depth threshold (SDI < 0.2). Lower is better.",
  },
  sdi_ap: {
    label: "Mean depth",
    hint: "Average sleep depth index during sleep. Higher means deeper sleep.",
  },
  sdi_cv: {
    label: "Depth variability",
    hint: "Coefficient of variation of depth across sleep. Lower is steadier.",
  },
  sdi_skew: {
    label: "Depth skew",
    hint: "Asymmetry of the depth distribution; negative leans shallow.",
  },
  sdi_mdr: {
    label: "REM depth",
    hint: "Mean depth during REM epochs (marked by the depth model).",
  },
  sdi_pr: {
    label: "REM prevalence",
    hint: "Share of sleep epochs the depth model flags as REM.",
  },
  sdi_mean_sleep: { label: "Mean sleep depth", hint: "SDI mean over sleep epochs." },
  sdi_std_sleep: { label: "Depth std", hint: "Standard deviation of SDI during sleep." },
  sdi_p05: { label: "Depth 5th pct", hint: "Shallow tail of the depth distribution." },
  sdi_p95: { label: "Depth 95th pct", hint: "Deep tail of the depth distribution." },
  sdi_shallow_minutes: { label: "Shallow minutes", hint: "Minutes of sleep below the depth threshold.", unit: "min" },
  sdi_deep_minutes: { label: "Deep minutes", hint: "Minutes of sleep at high depth.", unit: "min" },
  sdi_auc: { label: "Depth AUC", hint: "Total depth exposure across the night.", unit: "min" },
  sdi_apen: {
    label: "Approx. entropy",
    hint: "Predictability of the depth curve. Higher = more complex/fragmented.",
  },
  sdi_dfa: {
    label: "DFA α",
    hint: "Long-range correlation of the depth signal (detrended fluctuation analysis).",
  },
};
