"use client";

/**
 * SignalsExplorer
 * Raw waveform browser for the actual uploaded recording: whole-night decimated
 * preview per channel, window navigation, and a zoomed single-epoch view.
 */

import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, ZoomIn } from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle, InlineLoader } from "@/components/ui";
import { useEpochQuery, useSignalsQuery } from "@/lib/api/queries";
import type { SignalSeries, SignalsPreview } from "@/lib/api";
import { formatClock } from "@/lib/format";
import { cn } from "@/lib/utils";

const PREVIEW_WINDOWS = [
  { label: "10 min", duration: 600 },
  { label: "30 min", duration: 1800 },
  { label: "1 hour", duration: 3600 },
] as const;

export function SignalsExplorer({
  studyId,
  fileDurationSec,
  focusEpoch,
  onConsumed,
  className,
}: {
  studyId: string;
  fileDurationSec: number | null;
  /** Epoch index requested from elsewhere (e.g. hypnogram click). */
  focusEpoch?: number | null;
  onConsumed?: () => void;
  className?: string;
}) {
  const [startSec, setStartSec] = useState(0);
  const [windowSec, setWindowSec] = useState<number>(600);
  const [selectedChannels, setSelectedChannels] = useState<string[]>([]);
  const [zoomEpoch, setZoomEpoch] = useState<number | null>(null);

  useEffect(() => {
    if (typeof focusEpoch === "number") {
      setZoomEpoch(focusEpoch);
      onConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusEpoch]);

  const duration = Math.min(windowSec, Math.max(30, (fileDurationSec ?? windowSec) - startSec));
  const channelParam = selectedChannels.length ? selectedChannels.join(",") : undefined;
  const previewQuery = useSignalsQuery(studyId, {
    start_sec: startSec,
    duration_sec: duration,
    channels: channelParam,
  });

  const preview = previewQuery.data;
  const channels = preview?.channels ?? [];
  const availableChannels = preview?.available_channels ?? [];

  function navigate(direction: -1 | 1) {
    const step = duration;
    const max = Math.max(0, (fileDurationSec ?? step) - 30);
    setStartSec((current) => Math.min(max, Math.max(0, current + direction * step)));
  }

  return (
    <Card className={className}>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3 space-y-0 pb-3">
        <div>
          <CardTitle>Raw signals</CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            The uploaded recording itself — decimated min/max envelopes. Inspect before trusting any chart.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={() => navigate(-1)} aria-label="Earlier window">
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="min-w-28 text-center text-xs text-muted-foreground">
            {formatClock(startSec)} → {formatClock(startSec + duration)}
          </span>
          <Button variant="outline" size="icon" onClick={() => navigate(1)} aria-label="Later window">
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {PREVIEW_WINDOWS.map((option) => (
            <button
              key={option.label}
              onClick={() => setWindowSec(option.duration)}
              className={cn(
                "rounded-lg border px-2.5 py-1 text-xs transition-colors",
                windowSec === option.duration
                  ? "border-brand-bright bg-brand-light text-brand"
                  : "text-muted-foreground hover:bg-accent"
              )}
            >
              {option.label}
            </button>
          ))}
          <span className="mx-2 h-4 w-px bg-border" />
          <ChannelPicker
            available={availableChannels}
            selected={selectedChannels}
            onChange={setSelectedChannels}
          />
        </div>

        {/* Waveforms */}
        {previewQuery.isLoading ? (
          <div className="flex justify-center py-10">
            <InlineLoader />
          </div>
        ) : (
          <WaveformGrid preview={preview} onZoomEpoch={setZoomEpoch} />
        )}

        <p className="text-[11px] text-muted-foreground">
          Epochs are 30 s. Click an epoch number to inspect its waveform; use the zoom dialog to
          close the loop between raw signal and prediction.
        </p>

        {zoomEpoch !== null && (
          <EpochZoomDialog
            studyId={studyId}
            epochIndex={zoomEpoch}
            channels={channelParam}
            onClose={() => setZoomEpoch(null)}
          />
        )}
      </CardContent>
    </Card>
  );
}

function ChannelPicker({
  available,
  selected,
  onChange,
}: {
  available: { label: string; sample_rate: number }[];
  selected: string[];
  onChange: (next: string[]) => void;
}) {
  if (!available.length) return null;
  const isSelected = (label: string) =>
    selected.length === 0 || selected.includes(label);

  function toggle(label: string) {
    const next = selected.includes(label)
      ? selected.filter((candidate) => candidate !== label)
      : [...selected, label].slice(-8);
    onChange(next);
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {available.slice(0, 12).map((channel) => (
        <button
          key={channel.label}
          onClick={() => toggle(channel.label)}
          className={cn(
            "max-w-40 truncate rounded-full border px-2 py-0.5 text-[11px] transition-colors",
            isSelected(channel.label)
              ? "border-brand-bright/60 bg-brand-bright/10 text-brand"
              : "border-border text-muted-foreground hover:bg-accent"
          )}
          title={`${channel.label} @ ${channel.sample_rate} Hz`}
        >
          {channel.label}
        </button>
      ))}
    </div>
  );
}

function WaveformGrid({
  preview,
  onZoomEpoch,
}: {
  preview: SignalsPreview | undefined;
  onZoomEpoch: (epoch: number) => void;
}) {
  if (!preview?.series) return null;
  const labels = Object.keys(preview.series);
  if (!labels.length) return <p className="text-sm text-muted-foreground">No signal data.</p>;

  return (
    <div className="space-y-1">
      {labels.map((label) => (
        <WaveformRow key={label} label={label} series={preview.series[label]} />
      ))}
      <div className="flex items-center justify-between pt-1 text-[11px] text-muted-foreground">
        <span>Window: {preview.duration_sec.toFixed(0)} s</span>
        <EpochJump onJump={onZoomEpoch} />
      </div>
    </div>
  );
}

function WaveformRow({ label, series }: { label: string; series: SignalSeries }) {
  const path = useMemo(() => {
    const n = series.t?.length ?? 0;
    if (!n) return null;
    const points: string[] = [];
    if (series.v) {
      const v = series.v;
      const min = Math.min(...v);
      const max = Math.max(...v);
      const span = max - min || 1;
      v.forEach((value, index) => {
        points.push(`${((index / (n - 1)) * 100).toFixed(2)},${(100 - ((value - min) / span) * 100).toFixed(2)}`);
      });
    } else if (series.min && series.max) {
      const all = [...series.min, ...series.max];
      const min = Math.min(...all);
      const max = Math.max(...all);
      const span = max - min || 1;
      series.t.forEach((_, index) => {
        points.push(`${((index / (n - 1)) * 100).toFixed(2)},${(100 - ((series.max![index] - min) / span) * 100).toFixed(2)}`);
      });
      // Close the envelope back along the min curve
      for (let index = n - 1; index >= 0; index -= 1) {
        points.push(`${((index / (n - 1)) * 100).toFixed(2)},${(100 - ((series.min![index] - min) / span) * 100).toFixed(2)}`);
      }
    }
    if (!points.length) return null;
    return `M ${points.join(" L ")}`;
  }, [series]);

  return (
    <div className="flex items-center gap-2 border-b border-border/50 py-1.5 last:border-0">
      <span className="w-36 shrink-0 truncate text-right text-[11px] text-muted-foreground" title={label}>
        {label}
      </span>
      <div className="relative h-12 min-w-0 flex-1 overflow-hidden rounded-md bg-muted/30">
        {path && (
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full">
            <path d={path} fill={series.v ? "none" : "hsl(var(--brand-bright) / 0.15)"} stroke={series.v ? "hsl(var(--brand-bright))" : "none"} strokeWidth={series.v ? 0.4 : 0} vectorEffect="non-scaling-stroke" />
          </svg>
        )}
      </div>
    </div>
  );
}

function EpochJump({ onJump }: { onJump: (epoch: number) => void }) {
  const [value, setValue] = useState("");
  return (
    <span className="flex items-center gap-1.5">
      <ZoomIn className="h-3.5 w-3.5" />
      <input
        value={value}
        onChange={(event) => setValue(event.target.value.replace(/\D/g, ""))}
        placeholder="epoch #"
        className="h-6 w-20 rounded border border-input bg-card px-1.5 text-[11px]"
        aria-label="Epoch index to zoom into"
      />
      <Button variant="outline" size="sm" onClick={() => value && onJump(Number(value))}>
        Zoom
      </Button>
    </span>
  );
}

function EpochZoomDialog({
  studyId,
  epochIndex,
  channels,
  onClose,
}: {
  studyId: string;
  epochIndex: number;
  channels?: string;
  onClose: () => void;
}) {
  const epochQuery = useEpochQuery(studyId, epochIndex, channels);
  const series = epochQuery.data?.series ?? {};

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-brand-dark/40 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`Epoch ${epochIndex} waveform`}
    >
      <div
        className="max-h-[80vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-card p-6 shadow-soft"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Epoch {epochIndex}</h3>
            <p className="text-xs text-muted-foreground">
              {formatClock(epochIndex * 30)} – {formatClock((epochIndex + 1) * 30)} · 30 seconds
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
        {epochQuery.isLoading ? (
          <div className="flex justify-center py-10">
            <InlineLoader />
          </div>
        ) : (
          <WaveformGrid preview={epochQuery.data} onZoomEpoch={() => {}} />
        )}
      </div>
    </div>
  );
}
