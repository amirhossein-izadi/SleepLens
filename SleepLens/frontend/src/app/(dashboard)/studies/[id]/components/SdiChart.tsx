"use client";

import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { formatClock } from "@/lib/format";
import type { SdiPayload } from "@/lib/api";

/** Sleep depth index across the night with REM epoch markers. */
export function SdiChart({ sdi, className }: { sdi: SdiPayload | null; className?: string }) {
  const data = useMemo(() => {
    if (!sdi?.frames) return [];
    return sdi.frames.index.map((index, position) => ({
      index,
      time: formatClock(sdi.frames.start_sec[position]),
      sdi: sdi.frames.sdi[position],
      rem: sdi.frames.rem_pred[position] === 1,
    }));
  }, [sdi]);

  if (!data.length) return null;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Sleep depth index (SDI)</CardTitle>
        <p className="text-xs text-muted-foreground">
          {sdi?.sdi_note} · mean {sdi?.sdi_stats?.mean?.toFixed(2) ?? "—"} · range{" "}
          {sdi?.sdi_stats?.min?.toFixed(2) ?? "—"}–{sdi?.sdi_stats?.max?.toFixed(2) ?? "—"}
        </p>
      </CardHeader>
      <CardContent>
        {/* REM ribbon for context */}
        <div className="mb-2 flex h-3 w-full items-center gap-1.5">
          <span className="h-2 w-2 shrink-0 rounded-full bg-violet-500" title="REM epochs (depth model)" />
          <div className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-muted/50">
            {data.map((point) => (
              <div
                key={point.index}
                className="absolute h-full bg-violet-500/70"
                style={{
                  left: `${(point.index / data.length) * 100}%`,
                  width: `${100 / data.length + 0.05}%`,
                }}
              />
            ))}
          </div>
          <span className="shrink-0 text-[10px] text-muted-foreground">REM</span>
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
              <XAxis dataKey="time" tick={{ fontSize: 10 }} interval={Math.max(1, Math.floor(data.length / 8))} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 1]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={30} />
              <Tooltip
                contentStyle={{ borderRadius: 12, borderColor: "hsl(var(--border))" }}
                formatter={(value, name, item) => [
                  typeof value === "number" ? value.toFixed(2) : value,
                  item?.payload?.rem ? "SDI (REM epoch)" : name === "sdi" ? "Sleep depth" : name,
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
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
