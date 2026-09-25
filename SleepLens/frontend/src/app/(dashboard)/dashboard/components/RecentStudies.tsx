import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { formatDateTime, formatNumber } from "@/lib/format";import type { Study, StudyStatus } from "@/lib/api/types";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

const STATUS_VARIANT: Record<StudyStatus, "success" | "info" | "destructive" | "neutral"> = {
  completed: "success",
  processing: "info",
  uploaded: "neutral",
  failed: "destructive",
};

export function statusBadgeClass(status: StudyStatus): string {
  return status === "processing" ? "animate-pulse" : "";
}

export function StudyStatusBadge({ status }: { status: StudyStatus }) {
  return (
    <Badge variant={STATUS_VARIANT[status]} className={cn("capitalize", statusBadgeClass(status))}>
      {status}
    </Badge>
  );
}

export function RecentStudyRow({ study }: { study: Study }) {
  const meanConfidence = study.summary?.mean_confidence;
  return (
    <Link
      href={`/studies/${study.id}`}
      className="flex items-center justify-between gap-4 rounded-lg border border-transparent px-3 py-3 transition-colors hover:border-border hover:bg-accent/40"
    >
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{study.original_filename}</p>
        <p className="text-xs text-muted-foreground">
          {formatDateTime(study.created_at)}
          {typeof meanConfidence === "number" &&
            ` · confidence ${formatNumber(meanConfidence * 100, 1)}%`}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <StudyStatusBadge status={study.status} />
        <ArrowRight className="h-4 w-4 text-muted-foreground" />
      </div>
    </Link>
  );
}
