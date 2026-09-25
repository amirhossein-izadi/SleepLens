"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { STAGE_COLORS, STAGE_HINTS, STAGES, formatDuration, type Stage } from "@/lib/format";
import { formatMinutes } from "../utils";
import type { SscPayload } from "@/lib/api";

export function StageDistribution({ ssc, className }: { ssc: SscPayload | null; className?: string }) {
  if (!ssc?.stage_summary) return null;

  const data = STAGES.map((stage) => ({
    stage,
    ...ssc.stage_summary[stage],
  }));

  const totalSleepEpochs = STAGES.filter((stage) => stage !== "Wake").reduce(
    (sum, stage) => sum + ssc.stage_summary[stage].count,
    0
  );

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Sleep architecture</CardTitle>
        <p className="text-xs text-muted-foreground">
          Distribution over the sleep window (first→last sleep ±30 min wake trim, as in the
          benchmark) — the hypnogram above covers the full recording.
        </p>
      </CardHeader>
      <CardContent className="grid gap-6 md:grid-cols-2">
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="count"
                nameKey="stage"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={2}
                strokeWidth={0}
              >
                {data.map((entry) => (
                  <Cell key={entry.stage} fill={STAGE_COLORS[entry.stage as Stage]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name) => [`${value} epochs`, name]}
                contentStyle={{ borderRadius: 12, borderColor: "hsl(var(--border))" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <table className="w-full self-center text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground">
              <th className="pb-2 font-medium">Stage</th>
              <th className="pb-2 text-right font-medium">Time</th>
              <th className="pb-2 text-right font-medium">% of night</th>
              <th className="pb-2 text-right font-medium">% of sleep</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => {
              const pctOfSleep =
                totalSleepEpochs > 0 && row.stage !== "Wake"
                  ? (row.count / totalSleepEpochs) * 100
                  : null;
              return (
                <tr key={row.stage} className="border-t" title={STAGE_HINTS[row.stage as Stage]}>
                  <td className="py-2">
                    <span className="flex items-center gap-2 font-medium">
                      <span
                        className="h-3 w-3 rounded-sm"
                        style={{ backgroundColor: STAGE_COLORS[row.stage as Stage] }}
                      />
                      {row.stage}
                    </span>
                  </td>
                  <td className="py-2 text-right tabular-nums">
                    {formatDuration((row.count * ssc.epoch_seconds) / 60)}
                  </td>
                  <td className="py-2 text-right tabular-nums">{row.pct.toFixed(1)}%</td>
                  <td className="py-2 text-right tabular-nums">
                    {pctOfSleep !== null ? `${pctOfSleep.toFixed(1)}%` : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
