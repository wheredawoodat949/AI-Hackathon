import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { PerformanceChart } from "@/components/charts/PerformanceChart";
import { performance } from "@/data";
import { cn } from "@/lib/utils";

const ranges = ["6W", "12W", "Season"] as const;

export function PerformancePanel() {
  const [range, setRange] = useState<(typeof ranges)[number]>("12W");
  const data =
    range === "6W" ? performance.slice(-6) : performance;

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>Expected Goals Trend</CardTitle>
          <p className="mt-0.5 text-xs text-muted">
            Rolling xG created vs conceded
          </p>
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-line bg-surface-2/60 p-0.5">
          {ranges.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={cn(
                "rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors",
                range === r
                  ? "bg-white/[0.08] text-ink"
                  : "text-muted hover:text-ink",
              )}
            >
              {r}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-3 flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5 text-muted">
            <span className="h-2 w-2 rounded-full bg-accent" /> xG created
          </span>
          <span className="flex items-center gap-1.5 text-muted">
            <span className="h-2 w-2 rounded-full bg-neg" /> xG conceded
          </span>
        </div>
        <div className="h-[260px] w-full">
          <PerformanceChart data={data} />
        </div>
      </CardContent>
    </Card>
  );
}
