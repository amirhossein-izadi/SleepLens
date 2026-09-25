"use client";

import { Card, CardContent, CardHeader, CardTitle, Badge } from "@/components/ui";
import { formatNumber } from "@/lib/format";
import { SQI_FEATURE_META } from "../types";
import { formatMinutes } from "../utils";
import type { FeaturesPayload } from "@/lib/api";

interface FeatureMeta {
  label: string;
  hint: string;
  unit?: string;
}

const SSC_META: Record<string, FeatureMeta> = {
  sol_min: { label: "Sleep onset latency", unit: "min", hint: "Time to first sleep epoch." },
  waso_min: { label: "Wake after sleep onset", unit: "min", hint: "Awake time between sleep onset and end." },
  rem_lat_min: { label: "REM latency", unit: "min", hint: "Sleep onset to first REM episode." },
  n_awakenings: { label: "Awakenings", hint: "Wake episodes after initial sleep onset." },
  awakening_index: { label: "Awakening index", unit: "/h", hint: "Awakenings per hour of sleep." },
  n_stage_shifts: { label: "Stage changes", hint: "Transitions between stages." },
  shift_index: { label: "Shift index", unit: "/min", hint: "Stage changes per minute of sleep." },
  sfi: { label: "Sleep fragmentation index", hint: "Composite fragmentation measure." },
  n_rem_episodes: { label: "REM episodes", hint: "Number of distinct REM bouts." },
  mean_rem_bout_min: { label: "Mean REM bout", unit: "min", hint: "Average REM episode length." },
  longest_sleep_bout_min: { label: "Longest sleep bout", unit: "min", hint: "Longest uninterrupted sleep stretch." },
  mean_sleep_bout_min: { label: "Mean sleep bout", unit: "min", hint: "Average uninterrupted sleep stretch." },
  longest_wake_post_onset_min: { label: "Longest wake bout", unit: "min", hint: "Longest wake period after onset." },
  arousal_count: { label: "Arousals", hint: "Detected EEG arousals." },
  arousal_index: { label: "Arousal index", unit: "/h", hint: "Arousals per hour of sleep." },
  emg_median_uv: { label: "Chin EMG median", unit: "µV", hint: "Baseline muscle tone." },
  emg_rem_mean_uv: { label: "EMG in REM", unit: "µV", hint: "Should drop during REM (atonia)." },
  emg_nrem_mean_uv: { label: "EMG in NREM", unit: "µV", hint: "Muscle tone during NREM." },
  rem_atonia_ratio: { label: "REM atonia ratio", hint: "EMG drop in REM vs NREM. ~1 = healthy atonia." },
  movement_index: { label: "Movement index", hint: "Share of epochs with elevated movement." },
  eeg_epochs_analyzed: { label: "EEG epochs analyzed", hint: "Epochs with usable EEG features." },
};

function valueFor(key: string, value: unknown, unit?: string): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    if (unit === "min" && Math.abs(value) >= 60) return formatMinutes(value);
    const digits = Math.abs(value) >= 100 ? 0 : Math.abs(value) >= 1 ? 2 : 4;
    return `${formatNumber(value, digits)}${unit ? ` ${unit}` : ""}`;
  }
  return String(value);
}

function FeatureList({
  entries,
  meta,
}: {
  entries: [string, unknown][];
  meta: Record<string, FeatureMeta>;
}) {
  return (
    <div className="grid gap-x-8 gap-y-1.5 sm:grid-cols-2">
      {entries.map(([key, value]) => (
        <div
          key={key}
          className="flex items-center justify-between gap-3 border-b border-border/40 py-1.5"
          title={meta[key]?.hint}
        >
          <span className="text-xs text-muted-foreground">{meta[key]?.label ?? key}</span>
          <span className="text-sm font-medium tabular-nums">
            {valueFor(key, value, meta[key]?.unit)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function FeatureTables({
  features,
  className,
}: {
  features: FeaturesPayload | null;
  className?: string;
}) {
  if (!features) return null;
  const sscEntries = Object.entries(features.values?.ssc ?? {});
  const sqiEntries = Object.entries(features.values?.sqi ?? {});
  const notAssessable = features.not_assessable ?? [];

  return (
    <div className={className ?? "grid gap-6 lg:grid-cols-2"}>
      <Card>
        <CardHeader>
          <CardTitle>Staging features (SSC)</CardTitle>
          <p className="text-xs text-muted-foreground">
            Continuity and architecture metrics derived from the staging stream.
          </p>
        </CardHeader>
        <CardContent>
          {sscEntries.length ? (
            <FeatureList entries={sscEntries} meta={SSC_META} />
          ) : (
            <p className="text-sm text-muted-foreground">Not available for this study.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sleep-depth features (SQI)</CardTitle>
          <p className="text-xs text-muted-foreground">
            Derived from the SDI transformer stream — depth, stability and complexity.
          </p>
        </CardHeader>
        <CardContent>
          {sqiEntries.length ? (
            <FeatureList
              entries={sqiEntries}
              meta={SQI_FEATURE_META as unknown as Record<string, FeatureMeta>}
            />
          ) : (
            <p className="text-sm text-muted-foreground">Not available for this study.</p>
          )}
        </CardContent>
      </Card>

      {notAssessable.length > 0 && (
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Not assessable</CardTitle>
            <p className="text-xs text-muted-foreground">
              Features that need sensors this recording does not provide are excluded — never faked.
            </p>
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-2">
            {notAssessable.map((entry) => (
              <div key={entry.key} className="flex items-start gap-2 rounded-lg bg-muted/40 px-3 py-2">
                <Badge variant="neutral" className="shrink-0 text-[10px]">
                  {entry.key}
                </Badge>
                <p className="text-xs text-muted-foreground">{entry.reason}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
