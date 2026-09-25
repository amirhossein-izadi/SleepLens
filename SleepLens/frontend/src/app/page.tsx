import Link from "next/link";
import {
  ArrowRight,
  BrainCircuit,
  FileText,
  Gauge,
  HeartPulse,
  LineChart,
  ShieldCheck,
  Sparkles,
  Upload,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui";
import { Logo } from "@/components/brand/logo";
import { STAGE_COLORS, STAGES } from "@/lib/format";

const FEATURES = [
  {
    icon: BrainCircuit,
    title: "AI sleep staging",
    description:
      "A cohort-routed four-member ensemble classifies every 30-second epoch into Wake, N1, N2, N3 and REM.",
  },
  {
    icon: Gauge,
    title: "Sleep Quality Index",
    description:
      "A transparent 0–100 composite of efficiency, depth, continuity and REM architecture — no black box.",
  },
  {
    icon: LineChart,
    title: "Per-epoch confidence",
    description:
      "Every prediction ships with its full probability vector, a confidence band and a needs-review flag.",
  },
  {
    icon: HeartPulse,
    title: "Sleep depth index",
    description:
      "A continuous 0–1 depth curve across the night from the published SDI transformer, with REM windows marked.",
  },
  {
    icon: FileText,
    title: "LLM-written report",
    description:
      "A readable markdown narrative generated from the night's features, PSQI and summary — regenerate any time.",
  },
  {
    icon: Sparkles,
    title: "Expert assistant",
    description:
      "Chat with an AI assistant grounded in the case data — it answers from the actual metrics, nothing invented.",
  },
];

const PIPELINE = [
  {
    icon: Upload,
    title: "Upload the EDF",
    text: "Drop the recording, optionally link a patient and attach the PSQI questionnaire.",
  },
  {
    icon: BrainCircuit,
    title: "AI analyzes the night",
    text: "Ensemble staging + sleep-depth transformer score every 30-second epoch — 1–3 minutes.",
  },
  {
    icon: FileText,
    title: "Read the report",
    text: "Interactive hypnogram, confidence, quality index, raw signals and an AI narrative.",
  },
];

const STATS = [
  { value: "5-stage", label: "AASM sleep staging" },
  { value: "0–1", label: "Continuous sleep depth" },
  { value: "30 s", label: "Epoch-level confidence" },
  { value: "2 min", label: "Typical analysis time" },
];

export default function LandingPage() {
  return (
    <div className="min-h-dvh bg-background">
      {/* ── Nav ─────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Logo variant="full" className="h-9" priority />
          </Link>
          <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
            <a href="#features" className="transition-colors hover:text-foreground">
              Features
            </a>
            <a href="#pipeline" className="transition-colors hover:text-foreground">
              How it works
            </a>
            <a href="#report" className="transition-colors hover:text-foreground">
              The report
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <Button variant="ghost" asChild>
              <Link href="/login">Log in</Link>
            </Button>
            <Button variant="bright" asChild>
              <Link href="/register">Get started</Link>
            </Button>
          </div>
        </div>
      </header>

      <main>
        {/* ── Hero ──────────────────────────────────────────────────────── */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 [background:radial-gradient(ellipse_60%_50%_at_70%_20%,hsl(var(--brand-bright)/0.12),transparent)]" />
          <div className="container relative grid items-center gap-12 py-16 lg:grid-cols-2 lg:py-24">
            <div className="animate-fade-up space-y-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-brand-bright/25 bg-brand-light/60 px-3 py-1.5 text-xs font-medium text-brand">
                <Sparkles className="h-3.5 w-3.5" />
                Ensemble staging · Sleep depth · AI reporting
              </div>
              <h1 className="text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl">
                Your entire night,
                <br />
                <span className="brand-gradient-text">epoch by epoch.</span>
              </h1>
              <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
                Upload a polysomnography (EDF) recording and SleepLens classifies every 30-second
                epoch, models sleep depth, flags uncertain predictions for review, and writes the
                report — with the raw signals always one click away.
              </p>
              <div className="flex flex-wrap gap-3">
                <Button size="lg" variant="bright" asChild>
                  <Link href="/register">
                    Analyze your first night <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="/login">I already have an account</Link>
                </Button>
              </div>

              {/* Stage legend */}
              <div className="flex flex-wrap items-center gap-x-5 gap-y-2 pt-2">
                {STAGES.map((stage) => (
                  <div key={stage} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <span
                      className="h-3 w-3 rounded-sm"
                      style={{ backgroundColor: STAGE_COLORS[stage] }}
                    />
                    {stage}
                  </div>
                ))}
              </div>
            </div>

            {/* Hero visual with floating chips */}
            <div className="animate-fade-up relative">
              <div className="absolute -inset-6 rounded-[2rem] bg-brand-bright/10 blur-2xl" />
              <div className="relative overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/brand/hero.png"
                  alt="SleepLens dashboard preview"
                  className="h-full w-full object-cover"
                />
              </div>
              {/* Floating score chip */}
              <div className="absolute -left-4 top-8 hidden rounded-xl border bg-card/95 px-4 py-3 shadow-soft backdrop-blur sm:block">
                <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                  Sleep score
                </p>
                <p className="mt-0.5 flex items-baseline gap-1">
                  <span className="text-2xl font-bold text-brand-bright">92</span>
                  <span className="text-xs text-muted-foreground">/ 100</span>
                </p>
              </div>
              {/* Floating confidence chip */}
              <div className="absolute -bottom-4 right-6 hidden items-center gap-2.5 rounded-xl border bg-card/95 px-4 py-3 shadow-soft backdrop-blur sm:flex">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <div>
                  <p className="text-xs font-semibold">N3 · 96% confidence</p>
                  <p className="text-[10px] text-muted-foreground">02:41 — deep sleep</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Stats band ────────────────────────────────────────────────── */}
        <section className="border-y border-border/60 bg-primary text-primary-foreground">
          <div className="container grid grid-cols-2 gap-6 py-10 sm:grid-cols-4">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-2xl font-bold sm:text-3xl">{stat.value}</p>
                <p className="mt-1 text-xs text-primary-foreground/70">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Features ──────────────────────────────────────────────────── */}
        <section id="features" className="bg-card/50 py-20">
          <div className="container space-y-12">
            <div className="mx-auto max-w-2xl space-y-3 text-center">
              <p className="text-xs font-semibold uppercase tracking-widest text-brand-bright">
                Capabilities
              </p>
              <h2 className="text-3xl font-bold tracking-tight">
                From raw signal to understanding
              </h2>
              <p className="text-muted-foreground">
                SleepLens runs a complete pipeline on every recording — and shows you all of it.
              </p>
            </div>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map((feature) => (
                <div
                  key={feature.title}
                  className="group rounded-xl border bg-card p-6 shadow-soft transition-all hover:-translate-y-0.5 hover:shadow-md"
                >
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-brand-light transition-colors group-hover:bg-brand-bright/15">
                    <feature.icon className="h-5 w-5 text-brand-bright" />
                  </div>
                  <h3 className="mb-1.5 font-semibold">{feature.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Pipeline ──────────────────────────────────────────────────── */}
        <section id="pipeline" className="container py-20">
          <div className="mx-auto max-w-2xl space-y-3 text-center">
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-bright">
              How it works
            </p>
            <h2 className="text-3xl font-bold tracking-tight">Three steps, one night</h2>
          </div>
          <div className="relative mt-14 grid gap-8 md:grid-cols-3">
            {/* Connector line */}
            <div className="absolute left-[16%] right-[16%] top-8 hidden border-t-2 border-dashed border-brand-bright/30 md:block" />
            {PIPELINE.map((step, index) => (
              <div key={step.title} className="relative text-center md:px-4">
                <div className="relative z-10 mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border bg-card shadow-soft">
                  <step.icon className="h-7 w-7 text-brand-bright" />
                  <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-brand-bright text-xs font-bold text-white">
                    {index + 1}
                  </span>
                </div>
                <h3 className="mb-1.5 mt-5 font-semibold">{step.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{step.text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Report preview ────────────────────────────────────────────── */}
        <section id="report" className="border-y border-border/60 bg-card/50 py-20">
          <div className="container grid items-center gap-10 lg:grid-cols-2">
            <div className="space-y-6">
              <p className="text-xs font-semibold uppercase tracking-widest text-brand-bright">
                The report
              </p>
              <h2 className="text-3xl font-bold tracking-tight">
                A clinical report that explains itself
              </h2>
              <p className="leading-relaxed text-muted-foreground">
                The first page answers three questions immediately: how well did you sleep, what
                did the architecture look like, and what needs attention. Hover the hypnogram to
                see the model&apos;s exact reasoning for every epoch.
              </p>
              <ul className="space-y-3">
                {[
                  "Interactive hypnogram with per-epoch confidence and alternatives",
                  "Sleep Quality Score with a transparent weighted breakdown",
                  "Key findings, severity-flagged, derived from the real metrics",
                  "Raw signal viewer — verify any prediction against the recording",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm">
                    <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                    <span className="text-muted-foreground">{item}</span>
                  </li>
                ))}
              </ul>
              <Button variant="bright" asChild>
                <Link href="/register">
                  See it on your data <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>

            {/* Mini mock report card */}
            <div className="rounded-2xl border bg-card p-5 shadow-soft">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-300" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-300" />
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-300" />
                </div>
                <span className="text-[10px] text-muted-foreground">SleepLens Report</span>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-3">
                <div className="col-span-1 rounded-xl bg-brand-light/60 p-4 text-center">
                  <p className="text-3xl font-bold text-brand">82</p>
                  <p className="text-[10px] text-brand/70">/ 100 · Good</p>
                </div>
                <div className="col-span-2 grid grid-cols-2 gap-2">
                  {[
                    ["6h 02m", "Time asleep"],
                    ["89.5%", "Efficiency"],
                    ["62.5m", "REM latency"],
                    ["116", "Stage changes"],
                  ].map(([value, label]) => (
                    <div key={label} className="rounded-lg border bg-background p-2.5">
                      <p className="text-sm font-bold">{value}</p>
                      <p className="text-[10px] text-muted-foreground">{label}</p>
                    </div>
                  ))}
                </div>
              </div>
              {/* Mini hypnogram */}
              <svg viewBox="0 0 240 64" className="mt-4 w-full rounded-xl bg-muted/40 p-2" aria-hidden>
                {[
                  { y: 8, color: STAGE_COLORS.Wake, path: "M0,8 H20 L30,40 H45 L55,8 H60" },
                  { y: 24, color: STAGE_COLORS.REM, path: "" },
                  { y: 40, color: STAGE_COLORS.N1, path: "" },
                  { y: 56, color: STAGE_COLORS.N3, path: "" },
                ].map(
                  (row) =>
                    row.path && (
                      <path
                        key={row.y}
                        d={row.path}
                        fill="none"
                        stroke={row.color}
                        strokeWidth={2.5}
                        strokeLinejoin="round"
                      />
                    )
                )}
                <path
                  d="M0,8 L10,8 L10,24 L28,24 L28,8 L36,8 L36,56 L60,56 L60,40 L74,40 L74,56 L92,56 L92,24 L110,24 L110,56 L128,56 L128,24 L140,24 L140,8 L150,8 L150,24 L166,24 L166,40 L182,40 L182,56 L200,56 L200,24 L214,24 L214,40 L228,40 L228,8 L240,8"
                  fill="none"
                  stroke="hsl(var(--brand-bright))"
                  strokeWidth={2.5}
                  strokeLinejoin="round"
                />
              </svg>
              <div className="mt-3 flex justify-between text-[10px] text-muted-foreground">
                <span>23:30</span>
                <span>01:00</span>
                <span>03:00</span>
                <span>05:00</span>
              </div>
            </div>
          </div>
        </section>

        {/* ── For experts band ──────────────────────────────────────────── */}
        <section className="container py-20">
          <div className="flex flex-col items-center gap-6 rounded-2xl border bg-card p-8 text-center shadow-soft sm:p-12">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-light">
              <Users className="h-6 w-6 text-brand-bright" />
            </div>
            <h2 className="max-w-2xl text-2xl font-bold tracking-tight sm:text-3xl">
              Built for sleep experts, not spreadsheets
            </h2>
            <p className="max-w-xl text-muted-foreground">
              Manage a patient roster, upload nightly recordings, review flagged epochs against the
              raw signals, and let the AI draft the narrative — while you keep the final word.
            </p>
            <Button size="lg" variant="bright" asChild>
              <Link href="/register">
                Create your account <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </section>
      </main>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-border/60 py-8">
        <div className="container flex flex-col items-center justify-between gap-3 text-sm text-muted-foreground sm:flex-row">
          <Logo variant="full" className="h-8" />
          <span className="flex items-center gap-1.5">
            <HeartPulse className="h-4 w-4 text-brand-bright" />
            Research tool — not a medical diagnosis
          </span>
        </div>
      </footer>
    </div>
  );
}
