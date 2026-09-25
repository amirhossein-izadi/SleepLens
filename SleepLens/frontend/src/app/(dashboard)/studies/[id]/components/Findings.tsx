"use client";

import { AlertTriangle, CheckCircle2, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import type { Finding } from "../utils";
import { cn } from "@/lib/utils";

const ICONS = {
  ok: CheckCircle2,
  info: Info,
  watch: AlertTriangle,
} as const;

const TONES = {
  ok: "text-emerald-600 bg-emerald-50",
  info: "text-sky-600 bg-sky-50",
  watch: "text-amber-600 bg-amber-50",
} as const;

export function Findings({ findings, className }: { findings: Finding[]; className?: string }) {
  if (!findings.length) return null;
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Key findings</CardTitle>
        <p className="text-xs text-muted-foreground">
          Derived automatically from this night&apos;s metrics — informational, not diagnostic.
        </p>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {findings.map((finding, index) => {
          const Icon = ICONS[finding.severity];
          return (
            <div key={index} className="flex items-start gap-3 rounded-lg border border-transparent px-2 py-1.5 hover:bg-accent/30">
              <span className={cn("mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full", TONES[finding.severity])}>
                <Icon className="h-4 w-4" />
              </span>
              <p className="text-sm text-foreground/90">{finding.text}</p>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
