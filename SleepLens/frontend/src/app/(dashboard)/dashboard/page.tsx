"use client";

import Link from "next/link";
import {
  ArrowRight,
  BedDouble,
  CheckCircle2,
  Clock3,
  Gauge,
  Loader2,
  MoonStar,
} from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle, EmptyState, LoadingSpinner, PageHeader } from "@/components/ui";
import { useDashboard } from "./hooks";
import { RecentStudyRow } from "./components/RecentStudies";
import { formatNumber, formatPct } from "@/lib/format";

const KPI_META = [
  { key: "total", label: "Total studies", icon: MoonStar },
  { key: "completed", label: "Completed", icon: CheckCircle2 },
  { key: "processing", label: "In progress", icon: Loader2 },
] as const;

export default function DashboardPage() {
  const { stats, recent, isLoading } = useDashboard();

  if (isLoading) return <LoadingSpinner text="Loading your sleep lab…" />;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Your overnight recordings, pipeline status and quick access to reports."
        actions={
          <Button variant="bright" asChild>
            <Link href="/studies?upload=1">Upload a recording</Link>
          </Button>
        }
      />

      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {KPI_META.map((meta) => (
          <Card key={meta.key}>
            <CardContent className="flex items-center gap-4 pt-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-light">
                <meta.icon className="h-5 w-5 text-brand-bright" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats[meta.key]}</p>
                <p className="text-sm text-muted-foreground">{meta.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
        <Card>
          <CardContent className="flex items-center gap-4 pt-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-light">
              <Gauge className="h-5 w-5 text-brand-bright" />
            </div>
            <div>
              <p className="text-2xl font-bold">
                {stats.avgSleepPct !== null ? formatNumber(stats.avgSleepPct, 1) : "—"}
                <span className="text-sm font-normal text-muted-foreground">
                  {stats.avgSleepPct !== null ? "%" : ""}
                </span>
              </p>
              <p className="text-sm text-muted-foreground">Avg time asleep</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent studies */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Recent studies</CardTitle>
            <Button variant="link" size="sm" asChild>
              <Link href="/studies">
                All studies <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-1">
            {recent.length === 0 ? (
              <EmptyState
                icon={BedDouble}
                title="No studies yet"
                description="Upload a PSG (EDF) recording and SleepLens will analyze every 30-second epoch."
                action={
                  <Button variant="bright" asChild>
                    <Link href="/studies?upload=1">Upload your first night</Link>
                  </Button>
                }
              />
            ) : (
              recent.map((study) => <RecentStudyRow key={study.id} study={study} />)
            )}
          </CardContent>
        </Card>

        {/* Guidance */}
        <Card>
          <CardHeader>
            <CardTitle>What you can see</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {[
              { icon: BedDouble, text: "Interactive hypnogram with per-epoch predictions" },
              { icon: Gauge, text: "Sleep Quality Index and full metric cards" },
              { icon: Clock3, text: "Raw signal viewer across channels and epochs" },
              { icon: CheckCircle2, text: "Per-frame confidence with needs-review flags" },
            ].map((item, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-brand-light">
                  <item.icon className="h-4 w-4 text-brand-bright" />
                </div>
                <p className="text-muted-foreground">{item.text}</p>
              </div>
            ))}

            {stats.avgConfidence !== null && (
              <div className="rounded-lg bg-brand-light px-4 py-3">
                <p className="text-xs text-brand">MEAN STAGING CONFIDENCE</p>
                <p className="text-xl font-bold text-brand">{formatPct(stats.avgConfidence * 100)}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
