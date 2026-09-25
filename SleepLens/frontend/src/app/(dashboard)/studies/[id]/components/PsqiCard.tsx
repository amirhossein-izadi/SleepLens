"use client";

import { Card, CardContent, CardHeader, CardTitle, Badge } from "@/components/ui";
import type { PsqiPayload } from "@/lib/api";

const COMPONENT_LABELS: Record<string, string> = {
  c1: "Subjective sleep quality",
  c2: "Sleep latency",
  c3: "Sleep duration",
  c4: "Habitual sleep efficiency",
  c5: "Sleep disturbances",
  c6: "Use of sleeping medication",
  c7: "Daytime dysfunction",
};

export function PsqiCard({ psqi, className }: { psqi: PsqiPayload | null; className?: string }) {
  if (!psqi?.taken) return null;

  const score = psqi.global_score ?? 0;
  const tone = score <= 5 ? "success" : score <= 10 ? "warning" : "destructive";
  const interpretation =
    score <= 5 ? "Good sleep quality" : score <= 10 ? "Moderate difficulties" : "Poor sleep quality";

  return (
    <Card className={className}>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle>PSQI questionnaire</CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Self-reported sleep quality attached to this study.
          </p>
        </div>
        <Badge variant={tone}>Global {score}/21 · {interpretation}</Badge>
      </CardHeader>
      <CardContent>
        <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-muted">
          {Object.entries(psqi.components).map(([key, value]) => (
            <div
              key={key}
              title={`${COMPONENT_LABELS[key] ?? key}: ${value}/3`}
              style={{ width: `${(value / 21) * 100}%` }}
              className={
                score <= 5 ? "bg-emerald-500" : score <= 10 ? "bg-amber-500" : "bg-red-500"
              }
            />
          ))}
        </div>
        <div className="mt-3 grid gap-x-8 gap-y-1.5 sm:grid-cols-2">
          {Object.entries(psqi.components).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between gap-3 border-b border-border/40 py-1.5">
              <span className="text-xs text-muted-foreground">{COMPONENT_LABELS[key] ?? key}</span>
              <span className="text-sm font-medium tabular-nums">{value}/3</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
