"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import type { ScoreResult } from "@/lib/score";
import { cn } from "@/lib/utils";

const TONE: Record<ScoreResult["label"], string> = {
  Excellent: "text-emerald-600",
  Good: "text-brand-bright",
  Fair: "text-amber-600",
  Poor: "text-red-600",
};

/** Circular gauge for the composite SleepLens score. */
export function ScoreCard({ score, className }: { score: ScoreResult | null; className?: string }) {
  if (!score) return null;
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const progress = (score.score / 100) * circumference;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>SleepLens Score</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-5 sm:flex-row sm:items-center">
        <div className="relative h-32 w-32 shrink-0">
          <svg viewBox="0 0 128 128" className="h-full w-full -rotate-90">
            <circle cx={64} cy={64} r={radius} fill="none" stroke="hsl(var(--muted))" strokeWidth={10} />
            <circle
              cx={64}
              cy={64}
              r={radius}
              fill="none"
              stroke="url(#scoreGradient)"
              strokeWidth={10}
              strokeLinecap="round"
              strokeDasharray={`${progress} ${circumference}`}
            />
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="hsl(var(--brand-bright))" />
                <stop offset="100%" stopColor="hsl(var(--brand))" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold">{score.score}</span>
            <span className="text-[11px] text-muted-foreground">/ 100</span>
          </div>
        </div>
        <div className="w-full space-y-2">
          <p className={cn("text-lg font-semibold", TONE[score.label])}>{score.label} sleep quality</p>
          {score.breakdown.map((part) => (
            <div key={part.label} className="flex items-center gap-2 text-xs">
              <span className="w-24 shrink-0 text-muted-foreground">{part.label}</span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-brand-bright"
                  style={{ width: `${(part.value / part.max) * 100}%` }}
                />
              </div>
              <span className="w-8 text-right text-muted-foreground">{part.value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
