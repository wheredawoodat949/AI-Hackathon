import { motion } from "motion/react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { standings } from "@/data";
import { formatDelta } from "@/lib/format";
import { cn } from "@/lib/utils";

const formStyles: Record<string, string> = {
  W: "bg-pos/15 text-pos",
  D: "bg-white/[0.06] text-muted",
  L: "bg-neg/15 text-neg",
};

export function Leaderboard() {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>League Table</CardTitle>
          <p className="mt-0.5 text-xs text-muted">
            Apex Premier · Matchweek 12
          </p>
        </div>
        <span className="font-mono text-[11px] text-faint">xGD model v4.2</span>
      </CardHeader>
      <CardContent className="px-0 pb-2">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-line text-left text-[11px] uppercase tracking-wider text-faint">
                <th className="px-5 py-2 font-medium">#</th>
                <th className="px-2 py-2 font-medium">Club</th>
                <th className="px-2 py-2 text-center font-medium">P</th>
                <th className="px-2 py-2 text-center font-medium">W-D-L</th>
                <th className="px-2 py-2 text-right font-medium">xGD</th>
                <th className="px-2 py-2 text-center font-medium">Form</th>
                <th className="px-2 py-2 text-right font-medium">Win %</th>
                <th className="px-5 py-2 text-right font-medium">Pts</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((t, i) => (
                <motion.tr
                  key={t.id}
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.03 }}
                  className={cn(
                    "border-b border-line/60 transition-colors hover:bg-white/[0.02]",
                    t.rank === 1 && "bg-accent/[0.04]",
                  )}
                >
                  <td className="px-5 py-2.5">
                    <span
                      className={cn(
                        "tnum font-mono text-xs",
                        t.rank === 1 ? "text-accent" : "text-faint",
                      )}
                    >
                      {t.rank.toString().padStart(2, "0")}
                    </span>
                  </td>
                  <td className="px-2 py-2.5">
                    <div className="flex items-center gap-2.5">
                      <span className="grid h-7 w-7 place-items-center rounded-md border border-line bg-surface-2 font-mono text-[10px] font-semibold text-muted">
                        {t.short}
                      </span>
                      <span className="font-medium text-ink">{t.club}</span>
                    </div>
                  </td>
                  <td className="px-2 py-2.5 text-center tnum text-muted">
                    {t.played}
                  </td>
                  <td className="px-2 py-2.5 text-center tnum text-muted">
                    {t.won}-{t.drawn}-{t.lost}
                  </td>
                  <td
                    className={cn(
                      "px-2 py-2.5 text-right tnum font-medium",
                      t.xgDiff >= 0 ? "text-pos" : "text-neg",
                    )}
                  >
                    {formatDelta(t.xgDiff)}
                  </td>
                  <td className="px-2 py-2.5">
                    <div className="flex items-center justify-center gap-1">
                      {t.form.map((f, j) => (
                        <span
                          key={j}
                          className={cn(
                            "grid h-4 w-4 place-items-center rounded text-[9px] font-semibold",
                            formStyles[f],
                          )}
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-2 py-2.5 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="hidden h-1 w-12 overflow-hidden rounded-full bg-white/[0.06] sm:block">
                        <div
                          className="h-full rounded-full bg-accent"
                          style={{ width: `${t.winProb}%` }}
                        />
                      </div>
                      <span className="tnum w-10 text-right text-xs text-muted">
                        {t.winProb.toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-2.5 text-right tnum font-mono font-semibold text-ink">
                    {t.points}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
