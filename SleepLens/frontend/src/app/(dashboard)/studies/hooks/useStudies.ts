"use client";

/**
 * useStudies Hook
 * Manages the study list: search/status filters and upload-modal state.
 */

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useStudiesQuery } from "@/lib/api/queries";
import type { Study, StudyStatus } from "@/lib/api";

export interface UseStudiesReturn {
  studies: Study[];
  total: number;
  isLoading: boolean;
  search: string;
  setSearch: (value: string) => void;
  statusFilter: StudyStatus | "";
  setStatusFilter: (value: StudyStatus | "") => void;
  uploadOpen: boolean;
  setUploadOpen: (open: boolean) => void;
  isPolling: boolean;
}

export function useStudies(): UseStudiesReturn {
  const searchParams = useSearchParams();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StudyStatus | "">("");
  const [uploadOpen, setUploadOpen] = useState(searchParams.get("upload") === "1");

  const filters = useMemo(
    () => ({
      search: search.trim() || undefined,
      status: statusFilter || undefined,
    }),
    [search, statusFilter]
  );

  const { data, isLoading, isFetching } = useStudiesQuery(filters, true);

  const studies = data?.results ?? [];
  const isPolling =
    studies.some((study) => study.status === "processing" || study.status === "uploaded") ||
    false;

  return {
    studies,
    total: data?.total ?? 0,
    isLoading,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    uploadOpen,
    setUploadOpen,
    isPolling: isPolling || isFetching,
  };
}
