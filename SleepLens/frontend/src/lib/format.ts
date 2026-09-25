export const STAGES = ["Wake", "N1", "N2", "N3", "REM"] as const;
export type Stage = (typeof STAGES)[number];

/** Canonical stage palette — used by hypnogram, donut, legends and tables alike. */
export const STAGE_COLORS: Record<Stage, string> = {
  Wake: "#94a3b8",
  N1: "#93c5fd",
  N2: "#3b82f6",
  N3: "#1d4ed8",
  REM: "#8b5cf6",
};

export const STAGE_TAILWIND: Record<Stage, string> = {
  Wake: "bg-slate-400",
  N1: "bg-blue-300",
  N2: "bg-blue-500",
  N3: "bg-blue-700",
  REM: "bg-violet-500",
};

export const STAGE_HINTS: Record<Stage, string> = {
  Wake: "Awake during the recording window",
  N1: "Light drowsy sleep, easy to wake",
  N2: "Light stable sleep with sleep spindles",
  N3: "Deep restorative slow-wave sleep",
  REM: "Dreaming stage, key for memory and mood",
};

export function formatDuration(minutes: number | null | undefined): string {
  if (minutes === null || minutes === undefined) return "—";
  const totalMinutes = Math.round(minutes);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  if (h === 0) return `${m}m`;
  return `${h}h ${m.toString().padStart(2, "0")}m`;
}

export function formatClock(seconds: number): string {
  const date = new Date(seconds * 1000);
  const h = date.getUTCHours();
  const m = date.getUTCMinutes();
  const s = date.getUTCSeconds();
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s
    .toString()
    .padStart(2, "0")}`;
}

export function formatClockShort(seconds: number): string {
  const date = new Date(seconds * 1000);
  const h = date.getUTCHours();
  const m = date.getUTCMinutes();
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
}

export function formatPct(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(digits);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return "—";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}
