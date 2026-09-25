"use client";

import { useMemo, useRef, useState } from "react";
import { Eye, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Badge } from "@/components/ui";
import { STAGE_COLORS, STAGE_HINTS, formatClock, STAGES, type Stage } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { EpochDatum } from "../types";

/**
 * Hypnogram
 * True step rendering (horizontal hold, vertical jump at epoch boundaries),
 * fixed Wake/REM/N1/N2/N3 rows, hover tooltip with confidence + alternatives,
 * review markers and click-to-zoom support.
 */

/** Display order: Wake on top, then REM, N1, N2, N3 at the bottom. */
const ROWS: Stage[] = ["Wake", "REM", "N1", "N2", "N3"];
const ROW_HEIGHT = 26;
const HEADER_HEIGHT = 14;
const AXIS_HEIGHT = 26;
/** Left padding (% of width) so row labels never overlap the plot. */
const PAD_LEFT = 10;

const BAND_TONE: Record<EpochDatum["band"], string> = {
  high: "bg-emerald-100 text-emerald-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-red-100 text-red-700",
};

interface HoverState {
  epoch: EpochDatum;
  xPct: number;
}

interface HypnogramProps {
  epochs: EpochDatum[];
  epochSeconds: number;
  onEpochClick?: (epoch: EpochDatum) => void;
  className?: string;
}

export function Hypnogram({ epochs, epochSeconds, onEpochClick, className }: HypnogramProps) {
  const [detailed, setDetailed] = useState(true);
  const [hover, setHover] = useState<HoverState | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const n = epochs.length;
  const plotWidth = 100 - PAD_LEFT;
  const totalHeight = HEADER_HEIGHT + ROWS.length * ROW_HEIGHT + AXIS_HEIGHT;

  const geometry = useMemo(() => {
    const rowIndex = new Map(ROWS.map((stage, index) => [stage, index]));
    const rowY = (stage: Stage) =>
      HEADER_HEIGHT + (rowIndex.get(stage) ?? 0) * ROW_HEIGHT;
    const x = (index: number) => PAD_LEFT + (index / Math.max(1, n)) * plotWidth;
    const indexFromRatio = (ratio: number) => {
      const pct = ratio * 100;
      return Math.min(n - 1, Math.max(0, Math.floor(((pct - PAD_LEFT) / plotWidth) * n)));
    };
    return { rowIndex, rowY, x, indexFromRatio };
  }, [n, plotWidth]);

  /** Step path: horizontal to the boundary, then vertical to the next row. */
  const stepPath = useMemo(() => {
    if (!n) return "";
    let d = `M ${geometry.x(epochs[0].index).toFixed(2)},${rowCenterY(epochs[0], geometry)}`;
    for (let i = 1; i < n; i += 1) {
      const prevY = rowCenterY(epochs[i - 1], geometry);
      const currY = rowCenterY(epochs[i], geometry);
      const x = geometry.x(epochs[i].index).toFixed(2);
      d += ` L ${x},${prevY.toFixed(2)} L ${x},${currY.toFixed(2)}`;
    }
    // Hold the last stage to the right edge
    d += ` L 100,${rowCenterY(epochs[n - 1], geometry).toFixed(2)}`;
    return d;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [epochs, n, geometry]);

  function rowCenterY(epoch: EpochDatum, geom: typeof geometry): number {
    const stage = epoch.stageCode >= 0 ? STAGES[epoch.stageCode] : null;
    if (!stage) return HEADER_HEIGHT + ROWS.length * ROW_HEIGHT;
    return geom.rowY(stage) + ROW_HEIGHT / 2;
  }

  const xTicks = useMemo(() => {
    if (!n) return [];
    const targetTicks = 8;
    const step = Math.max(1, Math.round(n / targetTicks));
    const ticks: { index: number; label: string }[] = [];
    for (let index = 0; index < n; index += step) {
      ticks.push({ index, label: formatClock(epochs[index].startSec).slice(0, 5) });
    }
    return ticks;
  }, [n, epochs]);

  if (!n) return null;

  function handleMouseMove(event: React.MouseEvent<HTMLDivElement>) {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const ratio = (event.clientX - rect.left) / rect.width;
    const index = geometry.indexFromRatio(ratio);
    const epoch = epochs.find((candidate) => candidate.index === index);
    if (epoch) setHover({ epoch, xPct: geometry.x(index) });
  }

  return (
    <Card className={className}>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle>Sleep stages (hypnogram)</CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Hover an epoch for time, stage and confidence · click to inspect the raw signal.
          </p>
        </div>
        <button
          onClick={() => setDetailed((value) => !value)}
          className="flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent"
        >
          <Eye className="h-3.5 w-3.5" />
          {detailed ? "Detailed" : "Simple"}
        </button>
      </CardHeader>
      <CardContent>
        {/* Legend */}
        <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1.5">
          {STAGES.map((stage) => (
            <div
              key={stage}
              className="flex items-center gap-1.5 text-xs text-muted-foreground"
              title={STAGE_HINTS[stage]}
            >
              <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: STAGE_COLORS[stage] }} />
              {stage}
            </div>
          ))}
          {detailed && (
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="h-1.5 w-3 rounded-sm bg-red-300" />
              needs review
            </span>
          )}
        </div>

        <div
          ref={containerRef}
          className="relative cursor-crosshair select-none"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHover(null)}
          onClick={() => hover && onEpochClick?.(hover.epoch)}
          role="img"
          aria-label="Sleep hypnogram"
        >
          <svg
            viewBox={`0 0 100 ${totalHeight}`}
            preserveAspectRatio="none"
            className="block h-60 w-full"
          >
            {/* Row bands */}
            {ROWS.map((_, rowIndex) => (
              <rect
                key={rowIndex}
                x={PAD_LEFT - 1}
                y={HEADER_HEIGHT + rowIndex * ROW_HEIGHT}
                width={100 - PAD_LEFT + 1}
                height={ROW_HEIGHT}
                fill={rowIndex % 2 === 0 ? "hsl(var(--muted) / 0.4)" : "transparent"}
              />
            ))}
            {/* Row separators */}
            {ROWS.map((_, rowIndex) => (
              <line
                key={rowIndex}
                x1={PAD_LEFT - 1}
                x2={100}
                y1={HEADER_HEIGHT + rowIndex * ROW_HEIGHT}
                y2={HEADER_HEIGHT + rowIndex * ROW_HEIGHT}
                stroke="hsl(var(--border))"
                strokeWidth={0.3}
                vectorEffect="non-scaling-stroke"
              />
            ))}

            {/* Per-epoch stage blocks */}
            {epochs.map((epoch) => {
              const stage = epoch.stageCode >= 0 ? STAGES[epoch.stageCode] : null;
              if (!stage) return null;
              const row = geometry.rowIndex.get(stage) ?? ROWS.length - 1;
              return (
                <rect
                  key={epoch.index}
                  x={geometry.x(epoch.index)}
                  y={HEADER_HEIGHT + row * ROW_HEIGHT + 5}
                  width={plotWidth / n + 0.05}
                  height={ROW_HEIGHT - 10}
                  rx={0.4}
                  fill={STAGE_COLORS[stage]}
                  opacity={
                    detailed
                      ? epoch.band === "low"
                        ? 0.45
                        : epoch.band === "medium"
                          ? 0.75
                          : 1
                      : 0.9
                  }
                />
              );
            })}

            {/* Step line */}
            <path
              d={stepPath}
              fill="none"
              stroke="hsl(var(--brand))"
              strokeWidth={1.2}
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
              opacity={0.9}
            />

            {/* Hover crosshair */}
            {hover && (
              <line
                x1={geometry.x(hover.epoch.index)}
                x2={geometry.x(hover.epoch.index)}
                y1={HEADER_HEIGHT - 4}
                y2={totalHeight - AXIS_HEIGHT}
                stroke="hsl(var(--brand-bright))"
                strokeWidth={1}
                vectorEffect="non-scaling-stroke"
              />
            )}
          </svg>

          {/* Row labels overlay */}
          <div className="pointer-events-none absolute inset-0">
            {ROWS.map((stage, rowIndex) => (
              <span
                key={stage}
                className="absolute left-2 text-[10px] font-medium text-muted-foreground"
                style={{
                  top: `${((HEADER_HEIGHT + rowIndex * ROW_HEIGHT + ROW_HEIGHT / 2) / totalHeight) * 100}%`,
                  transform: "translateY(-50%)",
                }}
              >
                {stage}
              </span>
            ))}
          </div>

          {/* X axis labels */}
          <div className="pointer-events-none relative h-6">
            {xTicks.map((tick) => (
              <span
                key={tick.index}
                className="absolute -translate-x-1/2 whitespace-nowrap text-[10px] text-muted-foreground"
                style={{ left: `${geometry.x(tick.index)}%` }}
              >
                {tick.label}
              </span>
            ))}
            <span className="absolute right-0 text-[10px] text-muted-foreground">
              {formatClock(epochs[n - 1].startSec + epochSeconds).slice(0, 5)}
            </span>
          </div>

          {/* Review markers */}
          {detailed && (
            <div className="relative h-2" title="Epochs flagged needs_review">
              {epochs.map((epoch) =>
                epoch.needsReview ? (
                  <span
                    key={epoch.index}
                    className="absolute h-1.5 w-[2px] rounded bg-red-400"
                    style={{ left: `${geometry.x(epoch.index)}%` }}
                  />
                ) : null
              )}
            </div>
          )}

          {/* Tooltip */}
          {hover && (
            <EpochTooltip
              epoch={hover.epoch}
              xPct={hover.xPct}
              epochSeconds={epochSeconds}
              bandThresholds={null}
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function EpochTooltip({
  epoch,
  xPct,
  epochSeconds,
}: {
  epoch: EpochDatum;
  xPct: number;
  epochSeconds: number;
  bandThresholds: unknown;
}) {
  const ranked = epoch.probabilities
    .map((probability, index) => ({ stage: STAGES[index] as Stage, probability }))
    .sort((a, b) => b.probability - a.probability);
  const primary = ranked[0];
  const alternative = ranked[1];

  return (
    <div
      className="pointer-events-none absolute z-20 w-64 -translate-x-1/2 rounded-xl border bg-popover p-3 shadow-soft"
      style={{ left: `${Math.min(82, Math.max(18, xPct))}%`, top: 4 }}
    >
      <p className="text-xs font-medium text-muted-foreground">
        {formatClock(epoch.startSec)} – {formatClock(epoch.startSec + epochSeconds)}
      </p>
      <div className="mt-1.5 flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-sm font-semibold">
          <span
            className="h-3 w-3 rounded-sm"
            style={{ backgroundColor: primary ? STAGE_COLORS[primary.stage] : "transparent" }}
          />
          {primary?.stage ?? "—"}
        </span>
        <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-medium", BAND_TONE[epoch.band])}>
          {Math.round(epoch.confidence * 100)}% confidence
        </span>
      </div>
      {alternative && (
        <p className="mt-1 text-xs text-muted-foreground">
          Alternative: {alternative.stage} — {Math.round(alternative.probability * 100)}%
        </p>
      )}
      <div className="mt-2 space-y-1">
        {ranked.slice(0, 3).map((entry) => (
          <div key={entry.stage} className="flex items-center gap-2 text-[11px]">
            <span className="w-8 text-muted-foreground">{entry.stage}</span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${entry.probability * 100}%`,
                  backgroundColor: STAGE_COLORS[entry.stage],
                }}
              />
            </div>
            <span className="w-8 text-right text-muted-foreground">
              {Math.round(entry.probability * 100)}%
            </span>
          </div>
        ))}
      </div>
      <div className="mt-2 flex items-center justify-between border-t pt-2 text-[11px]">
        <span className="flex items-center gap-1 text-muted-foreground">
          <Info className="h-3 w-3" />
          prediction band
        </span>
        <span className={cn("rounded px-1.5 py-0.5 font-medium capitalize", BAND_TONE[epoch.band])}>
          {epoch.band}
        </span>
      </div>
      {epoch.needsReview && (
        <p className="mt-1 text-[11px] font-medium text-red-600">Flagged for expert review</p>
      )}
    </div>
  );
}
