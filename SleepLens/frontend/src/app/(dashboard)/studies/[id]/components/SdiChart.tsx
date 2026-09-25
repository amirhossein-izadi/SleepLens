"use client";

import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { formatClock } from "@/lib/format";
import { ema, contiguousRuns } from "@/lib/charts";
import type { SdiPayload } from "@/lib/api";

/** Sleep depth index across the night with REM markers + EMA smoothing. */
export function SdiChart({ sdi, className }: { sdi: SdiPayload | null; className?: string }) {
  const [smoothed, setSmoothed] = useState(false);

  const { data, remBands } = useMemo(() => {
    if (!sdi?.frames) return { data: [], remBands: [] as [number, number][] };
    const rawSdi = sdi.frames.index.map((_, position) => sdi.frames.sdi[position]);
    const series = smoothed ? ema(rawSdi, 30) : rawSdi;
    const rows = sdi.frames.index.map((_, position) => ({
      position,
      time: formatClock(sdi.frames.start_sec[position]),
      sdi: series[position],
      raw: rawSdi[position],
      rem: sdi.frames.rem_pred[position] === 1,
    }));
    const runs = contiguousRuns(
      rows.map((row) => row.rem),
      (flag) => flag
    );
    return { data: rows, remBands: runs };
  }, [sdi, smoothed]);

  if (!data.length) return null;

  return (
    <Card className={className}>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3 space-y-0 pb-2">
        <div>
          <CardTitle>Sleep depth index (SDI)</CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            {sdi?.sdi_note} · mean {sdi?.sdi_stats?.mean?.toFixed(2) ?? "—"} · range{" "}
            {sdi?.sdi_stats?.min?.toFixed(2) ?? "—"}–{sdi?.sdi_stats?.max?.toFixed(2) ?? "—"}
          </p>
        </div>
        <button
          onClick={() => setSmoothed((value) => !value)}
          className="rounded-lg border px-2.5 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent"
          title="Exponential moving average (span ≈ 30 epochs / 15 min)"
        >
          {smoothed ? "Smoothed (EMA 15 min)" : "Raw"}
        </button>
      </CardHeader>
      <CardContent>
        {/* REM ribbon (position-based; SDI-model REM head) */}
        <div className="mb-2 flex h-3 w-full items-center gap-1.5">
          <span
            className="h-2 w-2 shrink-0 rounded-full bg-violet-500"
            title="REM epochs (depth model REM head)"
          />
          <div className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-muted/50">
            {remBands.map(([start, end]) => (
              <div
                key={start}
                className="absolute h-full bg-violet-500/70"
                style={{
                  left: `${(start / data.length) * 100}%`,
                  width: `${((end - start + 1) / data.length) * 100}%`,
                }}
                title={`REM ${formatClock(sdi!.frames.start_sec[start])}`}
              />
            ))}
          </div>
          <span className="shrink-0 text-[10px] text-muted-foreground">
            REM {(remBands.reduce((sum, [start, end]) => sum + (end - start + 1), 0) * 100 / data.length).toFixed(0)}%
          </span>
        </div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="sdiFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--brand))" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="hsl(var(--brand-bright))" stopOpacity={0.03} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              {remBands.map(([start, end]) => (
                <ReferenceArea
                  key={`rem-${start}`}
                  x1={data[Math.max(0, start - 1)].time}
                  x2={data[Math.min(data.length - 1, end + 1)].time}
                  fill="#8b5cf6"
                  fillOpacity={0.12}
                  ifOverflow="extendDomain"
                />
              ))}
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10 }}
                interval={Math.max(1, Math.floor(data.length / 8))}
                tickLine={false}
                axisLine={false}
              />
              <YAxis domain={[0, 1]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={30} />
              <Tooltip
                contentStyle={{ borderRadius: 12, borderColor: "hsl(var(--border))" }}
                formatter={(value, name, item) => [
                  typeof value === "number" ? value.toFixed(2) : value,
                  item?.payload?.rem
                    ? name === "sdi"
                      ? "SDI (REM epoch)"
                      : name
                    : name === "sdi"
                      ? "Sleep depth"
                      : name,
                ]}
              />
              <ReferenceLine y={0.2} stroke="hsl(38 92% 44%)" strokeDasharray="4 4" label={{ value: "shallow threshold", fontSize: 10, position: "insideTopRight" }} />
              <Area
                type="monotone"
                dataKey="sdi"
                stroke="hsl(var(--brand))"
                strokeWidth={1.5}
                fill="url(#sdiFill)"
                connectNulls
                isAnimationActive={false}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        {smoothed && (
          <p className="mt-1 text-[10px] text-muted-foreground">
            EMA span ≈ 30 epochs (15 min) — hover still shows the exact epoch value.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
