import { TrendingUp } from "lucide-react";
import { PerformanceChart } from "@/components/charts/PerformanceChart";
import { Sparkline } from "@/components/ui/Sparkline";
import { kpis, performance, standings } from "@/data";

/** A realistic, static dashboard snapshot used as the hero showpiece. */
export function ProductPreview() {
  return (
    <div className="relative rounded-2xl border border-line-strong bg-panel/80 p-1.5 shadow-[0_40px_120px_-40px_rgba(0,0,0,0.9)] backdrop-blur-xl">
      {/* window chrome */}
      <div className="flex items-center gap-2 px-3 py-2">
        <span className="flex gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
          <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
          <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
        </span>
        <div className="mx-auto flex items-center gap-2 rounded-md border border-line bg-base/60 px-3 py-1 font-mono text-[10px] text-faint">
          app.apexanalytics.io/halston-city/overview
        </div>
      </div>

      <div className="rounded-xl border border-line bg-base/80 p-3 sm:p-4">
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          {/* KPI column */}
          <div className="flex flex-col gap-3">
            {kpis.slice(0, 3).map((k) => (
              <div
                key={k.id}
                className="rounded-xl border border-line bg-surface/70 p-3"
              >
                <p className="text-[11px] text-muted">{k.label}</p>
                <div className="mt-1 flex items-end justify-between">
                  <span className="font-mono text-xl font-semibold text-ink">
                    {k.value}
                  </span>
                  <Sparkline data={k.spark} width={64} height={28} />
                </div>
              </div>
            ))}
          </div>

          {/* Chart */}
          <div className="rounded-xl border border-line bg-surface/70 p-3 lg:col-span-2">
            <div className="mb-2 flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-ink">
                  Expected Goals Trend
                </p>
                <p className="text-[11px] text-faint">Halston City · 12 MW</p>
              </div>
              <span className="inline-flex items-center gap-1 rounded-full border border-accent/25 bg-accent/10 px-2 py-0.5 text-[10px] font-medium text-accent">
                <TrendingUp className="h-3 w-3" /> +0.31 xG
              </span>
            </div>
            <div className="h-[150px] sm:h-[180px]">
              <PerformanceChart data={performance} />
            </div>
          </div>
        </div>

        {/* mini table */}
        <div className="mt-3 hidden rounded-xl border border-line bg-surface/70 sm:block">
          {standings.slice(0, 3).map((t) => (
            <div
              key={t.id}
              className="flex items-center gap-3 border-b border-line/60 px-3 py-2 text-xs last:border-b-0"
            >
              <span className="w-4 font-mono text-faint">{t.rank}</span>
              <span className="grid h-6 w-6 place-items-center rounded border border-line bg-surface-2 font-mono text-[9px] text-muted">
                {t.short}
              </span>
              <span className="flex-1 font-medium text-ink">{t.club}</span>
              <span className="tnum text-pos">+{t.xgDiff}</span>
              <span className="tnum w-10 text-right font-mono font-semibold text-ink">
                {t.points} pts
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
