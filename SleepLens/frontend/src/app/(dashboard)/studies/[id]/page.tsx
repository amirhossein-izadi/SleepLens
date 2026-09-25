"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Download, RefreshCw } from "lucide-react";
import { AlertCircle, Clock3 } from "lucide-react";
import { API_ORIGIN } from "@/lib/api";
import type { StudyStatus } from "@/lib/api";
import { LoadingSpinner, Badge, Button, EmptyState } from "@/components/ui";
import { useToasts } from "@/components/ui/toast";
import { extractErrorMessage } from "@/lib/errorUtils";
import { formatDuration, formatDateTime } from "@/lib/format";
import { useReprocessMutation } from "@/lib/api/queries";
import { useStudyReport } from "./hooks";
import { buildFindings, buildKpis, computeScore, statusTone, type Finding } from "./utils";
import {
  Hypnogram,
  ScoreCard,
  KpiCards,
  StageDistribution,
  Findings,
  ConfidenceChart,
  SdiChart,
  SignalsExplorer,
  FeatureTables,
  PsqiCard,
  LlmReport,
  AssistantChat,
} from "./components";

interface ReportPageProps {
  params: { id: string };
}

export default function StudyReportPage({ params }: ReportPageProps) {
  const { id } = params;
  const { data, epochs, isAnalyzing, isFailed, isLoading } = useStudyReport(id);
  const reprocessMutation = useReprocessMutation(id);
  const { success, error } = useToasts();
  const [focusEpoch, setFocusEpoch] = useState<number | null>(null);

  if (isLoading || !data?.study) {
    return <LoadingSpinner text="Loading report…" />;
  }

  const { study, night, ssc, sdi, features, psqi, report } = data;
  const score = computeScore(night, sdi, features);
  const kpis = buildKpis(night, ssc, sdi, features);
  const findings = buildFindings(night, sdi, features);

  async function handleReprocess() {
    try {
      await reprocessMutation.mutateAsync();
      success("Reprocessing started");
    } catch (err) {
      error("Reprocess failed", extractErrorMessage(err, "Could not restart the pipeline."));
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <Link
            href="/studies"
            className="mt-1 flex h-8 w-8 items-center justify-center rounded-lg border text-muted-foreground transition-colors hover:bg-accent"
            aria-label="Back to studies"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {study.patient?.full_name || "Sleep Analysis Report"}
            </h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              {study.original_filename} · {formatDateTime(study.created_at)}
              {study.duration_minutes !== null && ` · ${formatDuration(study.duration_minutes)} recorded`}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleReprocess} loading={reprocessMutation.isPending}>
            <RefreshCw className="h-4 w-4" /> Reprocess
          </Button>
          <a href={`${API_ORIGIN}${study.download_url}`} target="_blank" rel="noreferrer">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4" /> Original EDF
            </Button>
          </a>
        </div>
      </div>

      {isAnalyzing && <AnalyzingBanner />}

      {isFailed && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
          <div>
            <p className="text-sm font-medium text-red-700">Analysis failed</p>
            <p className="text-xs text-red-600">
              {study.error_message || "The pipeline could not process this recording."} You can
              reprocess or download the file to inspect it.
            </p>
          </div>
        </div>
      )}

      {/* Main report (only when a night summary exists) */}
      {night && !isAnalyzing && (
        <>
          {/* Score + summary anchor */}
          <div className="grid gap-4 lg:grid-cols-3">
            <ScoreCard score={score} />
            <div className="lg:col-span-2">
              <SummaryCard
                label={score?.label ?? "—"}
                findings={findings}
                stagingSystem={night.staging_system ?? null}
                stagingMembers={night.staging_members?.length ?? null}
                meanConfidence={night.mean_confidence ?? null}
                reviewCount={night.needs_review_count ?? null}
                status={study.status}
              />
            </div>
          </div>

          {/* Hero: hypnogram (click an epoch to zoom into the raw signal) */}
          <Hypnogram
            epochs={epochs}
            epochSeconds={ssc?.epoch_seconds ?? 30}
            onEpochClick={(epoch) => setFocusEpoch(epoch.index)}
          />

          {/* KPI cards */}
          <KpiCards kpis={kpis} />

          {/* Architecture */}
          <StageDistribution ssc={ssc} />

          {/* Findings */}
          <Findings findings={findings} />

          {/* Confidence + depth */}
          <div className="grid gap-4 xl:grid-cols-2">
            <ConfidenceChart epochs={epochs} ssc={ssc} />
            <SdiChart sdi={sdi} />
          </div>

          {/* Raw signals */}
          <SignalsExplorer
            studyId={id}
            fileDurationSec={study.duration_minutes !== null ? study.duration_minutes * 60 : null}
            focusEpoch={focusEpoch}
            onConsumed={() => setFocusEpoch(null)}
          />

          {/* Features */}
          <FeatureTables features={features} />

          {/* PSQI */}
          <PsqiCard psqi={psqi} />

          {/* LLM report */}
          <LlmReport studyId={id} report={report} />

          {/* Assistant consultation (opencode-backed) */}
          <AssistantChat studyId={id} enabled={Boolean(features)} />
        </>
      )}

      {!night && !isAnalyzing && !isFailed && (
        <EmptyState
          icon={Clock3}
          title="Night summary not available"
          description="This study has not been analyzed yet. Run the pipeline to generate the report."
          action={
            <Button variant="bright" onClick={handleReprocess} loading={reprocessMutation.isPending}>
              Run analysis
            </Button>
          }
        />
      )}
    </div>
  );
}

function AnalyzingBanner() {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-sky-200 bg-sky-50 p-4">
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-sky-100">
        <Clock3 className="h-5 w-5 animate-pulse text-sky-600" />
      </span>
      <div>
        <p className="text-sm font-medium text-sky-800">Analysis in progress</p>
        <p className="text-xs text-sky-700">
          The pipeline is scoring every 30-second epoch — typically 1–3 minutes. This page updates
          automatically.
        </p>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  findings,
  stagingSystem,
  stagingMembers,
  meanConfidence,
  reviewCount,
  status,
}: {
  label: string;
  findings: Finding[];
  stagingSystem: string | null;
  stagingMembers: number | null;
  meanConfidence: number | null;
  reviewCount: number | null;
  status: StudyStatus;
}) {
  return (
    <div className="flex h-full flex-col justify-between rounded-xl border bg-card p-6 shadow-soft">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Overall summary
        </p>
        <p className="mt-2 text-lg font-semibold">{label} sleep quality</p>
        <div className="mt-3 space-y-1.5">
          {findings.slice(0, 3).map((finding, index) => (
            <p key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
              <span
                className={
                  finding.severity === "ok"
                    ? "mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500"
                    : finding.severity === "info"
                      ? "mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-500"
                      : "mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500"
                }
              />
              {finding.text}
            </p>
          ))}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2 border-t pt-4 text-xs text-muted-foreground">
        <Badge variant={statusTone(status)}>
          <span className="capitalize">{status}</span>
        </Badge>
        {stagingSystem && <Badge variant="outline">{stagingSystem}</Badge>}
        {stagingMembers !== null && <Badge variant="outline">{stagingMembers} models</Badge>}
        {meanConfidence !== null && (
          <Badge variant="outline">mean confidence {(meanConfidence * 100).toFixed(0)}%</Badge>
        )}
        {reviewCount !== null && reviewCount > 0 && (
          <Badge variant="warning">{reviewCount} epochs need review</Badge>
        )}
      </div>
    </div>
  );
}
