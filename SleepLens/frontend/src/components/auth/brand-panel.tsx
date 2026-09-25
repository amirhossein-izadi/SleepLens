import { STAGE_COLORS, STAGES } from "@/lib/format";
import { Logo } from "@/components/brand/logo";

/** Stage index (Wake=0,N1=1,N2=2,N3=3,REM=4) → display row in the hypnogram. */
const DISPLAY_ROW: Record<number, number> = { 0: 0, 1: 2, 2: 3, 3: 4, 4: 1 };
const PLOT_LEFT = 16;

/**
 * Decorative step path — true hypnogram behaviour: horizontal hold, then a
 * vertical jump at the epoch boundary. Never diagonal.
 */
function buildPath(): string {
  const stages = [0, 2, 2, 3, 3, 2, 4, 4, 2, 2, 1, 2, 3, 2, 2, 0, 1, 2, 2, 3, 2, 2, 4, 2, 1, 0];
  const step = (100 - PLOT_LEFT) / (stages.length - 1);
  let d = `M ${PLOT_LEFT},${DISPLAY_ROW[stages[0]] * 20}`;
  for (let i = 1; i < stages.length; i += 1) {
    const prevY = DISPLAY_ROW[stages[i - 1]] * 20;
    const currY = DISPLAY_ROW[stages[i]] * 20;
    const x = (PLOT_LEFT + i * step).toFixed(1);
    d += ` L ${x},${prevY} L ${x},${currY}`;
  }
  return d;
}

export function BrandPanel() {
  return (
    <div className="relative hidden overflow-hidden bg-primary lg:block">
      <div className="absolute inset-0 opacity-25 [background:radial-gradient(ellipse_at_30%_20%,_hsl(var(--brand-bright))_0%,_transparent_55%),radial-gradient(ellipse_at_80%_90%,_hsl(var(--brand-bright))_0%,_transparent_45%)]" />

      {/* Subtle grid texture */}
      <div className="absolute inset-0 opacity-[0.06] [background-image:linear-gradient(hsl(0_0%_100%)_1px,transparent_1px),linear-gradient(90deg,hsl(0_0%_100%)_1px,transparent_1px)] [background-size:56px_56px]" />

      <div className="relative flex h-full flex-col justify-between p-12 text-primary-foreground">
        <div className="w-fit rounded-2xl bg-white/95 px-5 py-3 shadow-soft">
          <Logo variant="full" className="h-9" priority />
        </div>

        <div className="max-w-md space-y-6">
          <h2 className="text-3xl font-bold leading-tight">
            Every epoch classified,
            <br />
            every decision explained.
          </h2>
          <p className="text-primary-foreground/75">
            SleepLens pairs an ensemble staging model with a sleep-depth transformer, then shows
            you the raw signals behind every prediction.
          </p>

          {/* Decorative hypnogram */}
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
            <svg viewBox="0 0 100 80" className="w-full" aria-hidden>
              {/* Row shading + labels */}
              {["Wake", "REM", "N1", "N2", "N3"].map((row, index) => (
                <g key={row}>
                  {index % 2 === 0 && (
                    <rect
                      x={PLOT_LEFT - 1}
                      y={index * 20}
                      width={100 - PLOT_LEFT + 2}
                      height={20}
                      fill="rgba(255,255,255,0.03)"
                    />
                  )}
                  <text x={0.5} y={index * 20 + 12.5} fill="rgba(255,255,255,0.5)" fontSize={4.2}>
                    {row}
                  </text>
                  <line
                    x1={PLOT_LEFT - 1}
                    x2={101}
                    y1={index * 20 + 20}
                    y2={index * 20 + 20}
                    stroke="rgba(255,255,255,0.08)"
                    strokeWidth={0.3}
                  />
                </g>
              ))}
              <path
                d={buildPath()}
                fill="none"
                stroke="hsl(var(--brand-bright))"
                strokeWidth={1.4}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            </svg>
            <div className="mt-3 flex gap-3">
              {STAGES.map((stage) => (
                <div
                  key={stage}
                  className="flex items-center gap-1.5 text-xs text-primary-foreground/70"
                >
                  <span
                    className="h-2.5 w-2.5 rounded-sm"
                    style={{ backgroundColor: STAGE_COLORS[stage] }}
                  />
                  {stage}
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {[
              { value: "5-stage", label: "AASM classification" },
              { value: "0–1", label: "Sleep depth index" },
              { value: "30 s", label: "Per-epoch confidence" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-xl border border-white/10 bg-white/5 p-3">
                <p className="text-sm font-bold">{stat.value}</p>
                <p className="mt-0.5 text-[10px] text-primary-foreground/60">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-primary-foreground/50">
          Research tool — not a medical diagnosis.
        </p>
      </div>
    </div>
  );
}
