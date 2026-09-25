/**
 * Client-side derivations for the report page: scoring, KPI extraction,
 * key findings and status interpretation. All inputs come from the backend
 * payloads; nothing is hardcoded per study.
 */

import type { NightPayload, SdiPayload, SscPayload, Study, FeaturesPayload } from "@/lib/api";
import { computeSleepScore, type ScoreResult } from "@/lib/score";
import { STAGES, type Stage } from "@/lib/format";

export interface Kpi {
  key: string;
  label: string;
  value: string;
  unit?: string;
  status?: "good" | "info" | "watch";
  hint?: string;
}

export interface Finding {
  severity: "ok" | "info" | "watch";
  text: string;
}

export function buildKpis(
  night: NightPayload | null,
  ssc: SscPayload | null,
  sdi: SdiPayload | null,
  features: FeaturesPayload | null
): Kpi[] {
  if (!night) return [];
  const hyp = (features?.values?.ssc ?? {}) as Record<string, unknown>;
  const num = (value: unknown): number | null =>
    typeof value === "number" && Number.isFinite(value) ? value : null;

  const sleepPct = night.sleep_pct;
  const shiftIndex = num(hyp["shift_index"]);
  const remLatency = num(hyp["rem_lat_min"]);
  const awakenings = num(hyp["n_awakenings"]);
  const remEpisodes = num(hyp["n_rem_episodes"]);
  const longestBout = num(hyp["longest_sleep_bout_min"]);
  const arousals = num(hyp["arousal_count"]);
  const arousalIndex = num(hyp["arousal_index"]);

  const stagePct = night.stage_pct ?? {};
  const n3Pct = stagePct["N3"];
  const remPct = stagePct["REM"];

  const kpis: Kpi[] = [
    {
      key: "tst",
      label: "Time asleep",
      value: formatMinutes((night.n_epochs ?? 0) * (sleepPct ?? 0) / 100 * 0.5),
      hint: "Estimated sleep time within the analyzed window.",
    },
    {
      key: "efficiency",
      label: "Sleep efficiency",
      value: sleepPct !== null && sleepPct !== undefined ? sleepPct.toFixed(1) : "—",
      unit: "%",
      status: sleepPct !== null && sleepPct !== undefined ? (sleepPct >= 85 ? "good" : sleepPct >= 70 ? "info" : "watch") : undefined,
      hint: "Share of the analyzed window spent asleep.",
    },
    {
      key: "sol",
      label: "Sleep onset latency",
      value: num(hyp["sol_min"]) !== null ? (num(hyp["sol_min"]) as number).toFixed(1) : "—",
      unit: "min",
      hint: "Time from lights-out window start to first sleep epoch.",
    },
    {
      key: "waso",
      label: "Wake after sleep onset",
      value: num(hyp["waso_min"]) !== null ? (num(hyp["waso_min"]) as number).toFixed(1) : "—",
      unit: "min",
      hint: "Total minutes awake between sleep onset and final wake-up.",
    },
    {
      key: "rem_latency",
      label: "REM latency",
      value: remLatency !== null ? remLatency.toFixed(1) : "—",
      unit: "min",
      hint: "Minutes from sleep onset to the first REM episode.",
    },
    {
      key: "deep",
      label: "Deep sleep (N3)",
      value: n3Pct !== null && n3Pct !== undefined ? n3Pct.toFixed(1) : "—",
      unit: "%",
      status: n3Pct !== null && n3Pct !== undefined ? (n3Pct >= 15 ? "good" : n3Pct >= 8 ? "info" : "watch") : undefined,
      hint: "Share of the window in slow-wave sleep.",
    },
    {
      key: "rem_share",
      label: "REM share",
      value: remPct !== null && remPct !== undefined ? remPct.toFixed(1) : "—",
      unit: "%",
      status: remPct !== null && remPct !== undefined ? (remPct >= 15 ? "good" : remPct >= 10 ? "info" : "watch") : undefined,
      hint: "Share of the window in REM sleep.",
    },
    {
      key: "shifts",
      label: "Stage changes",
      value: num(hyp["n_stage_shifts"]) !== null ? String(num(hyp["n_stage_shifts"])) : "—",
      status: shiftIndex !== null ? (shiftIndex < 1 ? "good" : shiftIndex < 2 ? "info" : "watch") : undefined,
      hint: "Transitions between sleep stages — a fragmentation proxy.",
    },
    {
      key: "confidence",
      label: "Mean confidence",
      value: night.mean_confidence !== null && night.mean_confidence !== undefined
        ? (night.mean_confidence * 100).toFixed(1)
        : "—",
      unit: "%",
      status: night.mean_confidence !== null && night.mean_confidence !== undefined
        ? night.mean_confidence >= 0.8 ? "good" : night.mean_confidence >= 0.6 ? "info" : "watch"
        : undefined,
      hint: "Average max-probability of the staging model across epochs.",
    },
    {
      key: "review",
      label: "Needs review",
      value: night.needs_review_pct !== null && night.needs_review_pct !== undefined
        ? night.needs_review_pct.toFixed(1)
        : "—",
      unit: "%",
      status: night.needs_review_pct !== null && night.needs_review_pct !== undefined
        ? night.needs_review_pct <= 10 ? "good" : night.needs_review_pct <= 30 ? "info" : "watch"
        : undefined,
      hint: "Epochs below the high-confidence threshold (review recommended).",
    },
  ];

  if (sdi?.sdi_stats?.mean !== null && sdi?.sdi_stats?.mean !== undefined) {
    kpis.push({
      key: "sdi_mean",
      label: "Mean sleep depth",
      value: sdi.sdi_stats.mean.toFixed(2),
      status: sdi.sdi_stats.mean >= 0.45 ? "good" : sdi.sdi_stats.mean >= 0.3 ? "info" : "watch",
      hint: "Sleep Depth Index (0–1); higher = deeper.",
    });
  }
  if (arousalIndex !== null) {
    kpis.push({
      key: "arousal_index",
      label: "Arousal index",
      value: arousalIndex.toFixed(1),
      unit: "/h",
      hint: "EEG arousals per hour of sleep.",
    });
  }
  if (arousals !== null && arousals > 0) {
    kpis.push({
      key: "arousals",
      label: "Arousals",
      value: String(arousals),
    });
  }
  if (awakenings !== null && awakenings > 0) {
    kpis.push({
      key: "awakenings",
      label: "Awakenings",
      value: String(awakenings),
      hint: "Wake episodes after initial sleep onset.",
    });
  }
  if (remEpisodes !== null && remEpisodes > 0) {
    kpis.push({
      key: "rem_episodes",
      label: "REM episodes",
      value: String(remEpisodes),
    });
  }
  if (longestBout !== null) {
    kpis.push({
      key: "longest_bout",
      label: "Longest sleep bout",
      value: formatMinutes(longestBout),
    });
  }
  return kpis;
}

export function computeScore(
  night: NightPayload | null,
  sdi: SdiPayload | null,
  features: FeaturesPayload | null
): ScoreResult | null {
  if (!night) return null;
  const hyp = (features?.values?.ssc ?? {}) as Record<string, unknown>;
  const num = (value: unknown): number | null =>
    typeof value === "number" && Number.isFinite(value) ? value : null;
  return computeSleepScore({
    sleepPct: night.sleep_pct,
    meanConfidence: night.mean_confidence,
    n3Pct: night.stage_pct?.N3 ?? null,
    remPct: night.stage_pct?.REM ?? null,
    shiftIndex: num(hyp["shift_index"]),
    solMin: num(hyp["sol_min"]),
    wasoMin: num(hyp["waso_min"]),
    sdiMean: sdi?.sdi_stats?.mean ?? null,
    sdiRb: (features?.values?.sqi as Record<string, unknown> | undefined)?.sdi_rb as number | null ?? null,
  });
}

export function buildFindings(
  night: NightPayload | null,
  sdi: SdiPayload | null,
  features: FeaturesPayload | null
): Finding[] {
  if (!night) return [];
  const findings: Finding[] = [];
  const hyp = (features?.values?.ssc ?? {}) as Record<string, unknown>;
  const sqi = (features?.values?.sqi ?? {}) as Record<string, unknown>;
  const num = (value: unknown): number | null =>
    typeof value === "number" && Number.isFinite(value) ? value : null;

  const sleepPct = night.sleep_pct;
  if (typeof sleepPct === "number") {
    findings.push(
      sleepPct >= 85
        ? { severity: "ok", text: `Sleep efficiency was high at ${sleepPct.toFixed(1)}%.` }
        : sleepPct >= 70
          ? { severity: "info", text: `Sleep efficiency was moderate at ${sleepPct.toFixed(1)}%.` }
          : { severity: "watch", text: `Sleep efficiency was low at ${sleepPct.toFixed(1)}%.` }
    );
  }

  const n3 = night.stage_pct?.N3;
  if (typeof n3 === "number") {
    findings.push(
      n3 >= 15
        ? { severity: "ok", text: `Deep sleep made up ${n3.toFixed(1)}% of the window — a solid slow-wave share.` }
        : { severity: "watch", text: `Deep sleep was limited at ${n3.toFixed(1)}% of the window.` }
    );
  }

  const rem = night.stage_pct?.REM;
  if (typeof rem === "number") {
    findings.push(
      rem >= 15
        ? { severity: "ok", text: `REM sleep was well represented at ${rem.toFixed(1)}%.` }
        : { severity: "info", text: `REM sleep was relatively limited at ${rem.toFixed(1)}%.` }
    );
  }

  const shifts = num(hyp["n_stage_shifts"]);
  if (shifts !== null) {
    findings.push(
      shifts > 90
        ? { severity: "watch", text: `Sleep fragmentation detected with ${shifts} stage changes.` }
        : { severity: "ok", text: `Stage continuity was reasonable with ${shifts} stage changes.` }
    );
  }

  const remLatency = num(hyp["rem_lat_min"]);
  if (remLatency !== null && remLatency > 120) {
    findings.push({
      severity: "info",
      text: `First REM episode arrived late (${remLatency.toFixed(0)} min after sleep onset).`,
    });
  }

  const reviewPct = night.needs_review_pct;
  if (typeof reviewPct === "number" && reviewPct > 25) {
    findings.push({
      severity: "watch",
      text: `${reviewPct.toFixed(0)}% of epochs fall below the high-confidence band — manual review recommended.`,
    });
  }

  const shallow = num(sqi["sdi_rb"]);
  if (shallow !== null) {
    findings.push(
      shallow > 0.45
        ? { severity: "watch", text: `Shallow-sleep burden was elevated: ${(shallow * 100).toFixed(0)}% of sleep below the depth threshold.` }
        : { severity: "ok", text: `Shallow-sleep burden was contained at ${(shallow * 100).toFixed(0)}% of sleep.` }
    );
  }

  const remPrevalence = num(sqi["sdi_pr"]);
  if (remPrevalence !== null && remPrevalence > 0) {
    findings.push({
      severity: "info",
      text: `The depth model flagged REM-like activity in ${(remPrevalence * 100).toFixed(0)}% of sleep.`,
    });
  }

  return findings;
}

export function statusTone(status: Study["status"]): "success" | "info" | "destructive" | "neutral" {
  switch (status) {
    case "completed":
      return "success";
    case "processing":
      return "info";
    case "failed":
      return "destructive";
    default:
      return "neutral";
  }
}

function formatMinutes(minutes: number): string {
  const total = Math.max(0, Math.round(minutes));
  const h = Math.floor(total / 60);
  const m = total % 60;
  return h > 0 ? `${h}h ${String(m).padStart(2, "0")}m` : `${m}m`;
}

export { formatMinutes };

/** Order stages for the architecture table: Wake last, N1..N3, REM before Wake. */
export const ARCHITECTURE_ORDER: Stage[] = ["REM", "N1", "N2", "N3", "Wake"];

export const ALL_STAGES = STAGES;
