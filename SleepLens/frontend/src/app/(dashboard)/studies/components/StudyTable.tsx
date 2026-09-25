import Link from "next/link";
import { MoreHorizontal, Trash2 } from "lucide-react";
import type { Study } from "@/lib/api";
import { Badge, InlineLoader } from "@/components/ui";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui";
import { formatBytes, formatDateTime, formatNumber } from "@/lib/format";

interface StudyTableProps {
  studies: Study[];
  onDelete: (id: string) => void;
  deletingId: string | null;
}

export function StudyTable({ studies, onDelete, deletingId }: StudyTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border bg-card shadow-soft">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
            <th className="px-4 py-3 font-medium">Recording</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Time asleep</th>
            <th className="px-4 py-3 font-medium">Confidence</th>
            <th className="px-4 py-3 font-medium">Uploaded</th>
            <th className="px-4 py-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {studies.map((study) => (
            <tr key={study.id} className="border-b transition-colors last:border-0 hover:bg-accent/40">
              <td className="max-w-xs px-4 py-3">
                <Link href={`/studies/${study.id}`} className="block">
                  <p className="truncate font-medium text-brand hover:underline">
                    {study.original_filename}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatBytes(study.file_size)}
                    {study.patient ? ` · ${study.patient.full_name}` : ""}
                  </p>
                </Link>
              </td>
              <td className="px-4 py-3">
                <Badge
                  variant={
                    study.status === "completed"
                      ? "success"
                      : study.status === "failed"
                        ? "destructive"
                        : study.status === "processing"
                          ? "info"
                          : "neutral"
                  }
                  className={study.status === "processing" ? "animate-pulse" : ""}
                >
                  <span className="capitalize">{study.status}</span>
                </Badge>
              </td>
              <td className="px-4 py-3">
                {typeof study.summary?.sleep_pct === "number"
                  ? formatNumber(study.summary.sleep_pct, 1) + "%"
                  : "—"}
              </td>
              <td className="px-4 py-3">
                {typeof study.summary?.mean_confidence === "number"
                  ? formatNumber(study.summary.mean_confidence * 100, 1) + "%"
                  : "—"}
              </td>
              <td className="px-4 py-3 text-muted-foreground">{formatDateTime(study.created_at)}</td>
              <td className="px-4 py-3 text-right">
                {deletingId === study.id ? (
                  <InlineLoader />
                ) : (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        className="rounded-md p-1.5 text-muted-foreground hover:bg-muted"
                        aria-label="Study actions"
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onDelete(study.id)} className="text-red-600">
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
