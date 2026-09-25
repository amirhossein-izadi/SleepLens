"use client";

import { useState } from "react";
import { MoonStar, Search, Upload } from "lucide-react";
import { Button, EmptyState, Input, LoadingSpinner, PageHeader, useToasts } from "@/components/ui";
import { useDeleteStudyMutation } from "@/lib/api/queries";
import { extractErrorMessage } from "@/lib/errorUtils";
import { useStudies } from "./hooks";
import { StudyTable, UploadDialog } from "./components";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "uploaded", label: "Uploaded" },
  { value: "processing", label: "Processing" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
] as const;

export default function StudiesPage() {
  const {
    studies,
    total,
    isLoading,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    uploadOpen,
    setUploadOpen,
    isPolling,
  } = useStudies();
  const deleteMutation = useDeleteStudyMutation();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const { success, error } = useToasts();

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await deleteMutation.mutateAsync(id);
      success("Study deleted");
    } catch (err) {
      error("Delete failed", extractErrorMessage(err, "Could not delete the study."));
    } finally {
      setDeletingId(null);
    }
  }

  if (isLoading) return <LoadingSpinner text="Loading studies…" />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Studies"
        description={`${total} recording${total === 1 ? "" : "s"}${isPolling ? " · updating…" : ""}`}
        actions={
          <Button variant="bright" onClick={() => setUploadOpen(true)}>
            <Upload className="h-4 w-4" /> Upload study
          </Button>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by filename…"
            className="pl-9"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}
          className="h-10 rounded-lg border border-input bg-card px-3 text-sm"
          aria-label="Filter by status"
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {studies.length === 0 ? (
        <EmptyState
          icon={MoonStar}
          title="No studies match"
          description="Upload a PSG (EDF) recording to start your first analysis."
          action={
            <Button variant="bright" onClick={() => setUploadOpen(true)}>
              <Upload className="h-4 w-4" /> Upload study
            </Button>
          }
        />
      ) : (
        <StudyTable studies={studies} onDelete={handleDelete} deletingId={deletingId} />
      )}

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </div>
  );
}
