/**
 * SleepLens composite score (0-100).
 *
 * Deliberately transparent: a weighted blend of the metrics the pipeline
 * already produces — architecture, continuity and sleep depth. It is a
 * product-level summary, not a clinical diagnosis.
 */

export interface ScoreInput {
  /** % of the analyzed window spent asleep (0-100). */
  sleepPct?: number | null;
  /** Mean staging confidence (0-1). */
  meanConfidence?: number | null;
  /** Deep sleep share of sleep time (0-100). */
  n3Pct?: number | null;
  /** REM share of sleep time (0-100). */
  remPct?: number | null;
  /** Sleep fragmentation index (shifts per minute of sleep). */
  shiftIndex?: number | null;
  /** Sleep onset latency in minutes. */
  solMin?: number | null;
  /** Wake after sleep onset in minutes. */
  wasoMin?: number | null;
  /** Mean sleep depth index (0-1). */
  sdiMean?: number | null;
  /** Shallow-sleep burden (fraction of sleep below the depth threshold). */
  sdiRb?: number | null;
}

export interface ScoreResult {
  score: number;
  label: "Poor" | "Fair" | "Good" | "Excellent";
  breakdown: { label: string; value: number; max: number }[];
}

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

export function computeSleepScore(input: ScoreInput): ScoreResult {
  const efficiency = clamp(((input.sleepPct ?? 0) - 55) / 40, 0, 1); // 55% → 0, 95%+ → 1
  const depth = clamp(((input.sdiMean ?? 0) - 0.25) / 0.45, 0, 1);
  const deepShare = clamp(((input.n3Pct ?? 0) - 5) / 20, 0, 1); // 5% → 0, 25%+ → 1
  const remShare = clamp(((input.remPct ?? 0) - 10) / 15, 0, 1); // 10% → 0, 25% → 1
  const continuity = clamp(1 - (input.shiftIndex ?? 1.5) / 2.5, 0, 1);
  const onset = clamp(1 - (input.solMin ?? 30) / 30, 0, 1);
  const fragmentation = clamp(1 - (input.sdiRb ?? 0.5) / 0.6, 0, 1);

  const parts = [
    { label: "Efficiency", value: efficiency * 25, max: 25 },
    { label: "Depth", value: depth * 25, max: 25 },
    { label: "Continuity", value: continuity * 20, max: 20 },
    { label: "Deep sleep", value: deepShare * 10, max: 10 },
    { label: "REM", value: remShare * 10, max: 10 },
    { label: "Onset", value: onset * 5, max: 5 },
    { label: "Fragmentation", value: fragmentation * 5, max: 5 },
  ];
  const score = Math.round(parts.reduce((sum, part) => sum + part.value, 0));

  return {
    score,
    label: score >= 80 ? "Excellent" : score >= 65 ? "Good" : score >= 45 ? "Fair" : "Poor",
    breakdown: parts.map((part) => ({ ...part, value: Math.round(part.value) })),
  };
}
