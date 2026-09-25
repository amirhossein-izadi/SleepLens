"use client";

import { HelpCircle } from "lucide-react";
import type { Kpi } from "../utils";
import { cn } from "@/lib/utils";

const TONE_CLASS = {
  good: "bg-emerald-50 text-emerald-700",
  info: "bg-sky-50 text-sky-700",
  watch: "bg-amber-50 text-amber-700",
} as const;

export function KpiCards({ kpis }: { kpis: Kpi[] }) {
  if (!kpis.length) return null;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {kpis.map((kpi) => (
        <div
          key={kpi.key}
          className="group relative rounded-xl border bg-card p-4 shadow-soft"
          title={kpi.hint}
        >
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">{kpi.label}</p>
            {kpi.hint && (
              <HelpCircle className="h-3.5 w-3.5 shrink-0 text-muted-foreground/60 group-hover:text-brand-bright" />
            )}
          </div>
          <p className="mt-1.5 text-xl font-bold">
            {kpi.value}
            {kpi.unit && <span className="ml-1 text-sm font-normal text-muted-foreground">{kpi.unit}</span>}
          </p>
          {kpi.status && (
            <span
              className={cn(
                "mt-2 inline-block rounded px-1.5 py-0.5 text-[10px] font-medium capitalize",
                TONE_CLASS[kpi.status]
              )}
            >
              {kpi.status === "good" ? "Good" : kpi.status === "info" ? "Fair" : "Watch"}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
