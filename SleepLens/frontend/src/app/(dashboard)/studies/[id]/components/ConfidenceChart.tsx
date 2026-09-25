"use client";

import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, Badge } from "@/components/ui";
import { STAGE_COLORS, STAGES, formatClock } from "@/lib/format";
import type { EpochDatum } from "../types";
import type { SscPayload } from "@/lib/api";

/**
 * Per-frame model confidence: line = confidence, shaded = low-confidence
 * regions, dashed lines = band thresholds. Stage ribbon underneath for context.
 */
export function ConfidenceChart({
  epochs,
  ssc,
  className,
}: {
  epochs: EpochDatum[];
  ssc: SscPayload | null;
  className?: string;
}) {
  const [showStageRibbon, setShowStageRibbon] = useState(true);
  const bands = ssc?.confidence_bands ?? { high: 0.8, medium: 0.6 };

  const data = useMemo(
    () =>
      epochs.map((epoch) => ({
        index: epoch.index,
        time: formatClock(epoch.startSec),
        confidence: Math.round(epoch.confidence * 1000) / 10,
        band: epoch.band,
        stageCode: epoch.stageCode,
        needsReview: epoch.needsReview,
      })),
    [epochs]
  );

  if (!data.length) return null;

  const maxConfidence = Math.max(...data.map((point) => point.confidence), 100);

  return (
    <Card className={className}>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle>Prediction confidence per epoch</CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Max class probability. Amber below {Math.round(bands.high * 100)}%, red below{" "}
            {Math.round(bands.medium * 100)}%.
          </p>
        </div>
        <Badge variant={data.some((point) => point.needsReview) ? "warning" : "success"}>
          {data.filter((point) => point.needsReview).length} flagged
        </Badge>
      </CardHeader>
      <CardContent>
        {showStageRibbon && (
          <div className="mb-2 flex h-3 w-full overflow-hidden rounded-full">
            {data.map((point, position) => (
              <div
                key={point.index}
                className="h-full"
                style={{
                  width: `${100 / data.length}%`,
                  backgroundColor:
                    point.stageCode >= 0 ? STAGE_COLORS[STAGES[point.stageCode]] : "transparent",
                  opacity: point.stageCode >= 0 ? 0.85 : 0,
                }}
                title={`${point.time} · ${STAGES[point.stageCode] ?? "?"}`}
              />
            ))}
          </div>
        )}
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="confFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--brand-bright))" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="hsl(var(--brand-bright))" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} interval={Math.max(1, Math.floor(data.length / 8))} tickLine={false} axisLine={false} />
              <YAxis domain={[0, maxConfidence]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} unit="%" width={38} />
              <Tooltip
                contentStyle={{ borderRadius: 12, borderColor: "hsl(var(--border))" }}
                formatter={(value, name) => [`${value}%`, name === "confidence" ? "Confidence" : name]}
              />
              <ReferenceLine y={bands.high * 100} stroke="hsl(152 60% 36%)" strokeDasharray="4 4" />
              <ReferenceLine y={bands.medium * 100} stroke="hsl(38 92% 44%)" strokeDasharray="4 4" />
              <Area
                type="monotone"
                dataKey="confidence"
                stroke="hsl(var(--brand-bright))"
                strokeWidth={1.5}
                fill="url(#confFill)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
