import { useState } from "react";
import { motion } from "motion/react";
import { ArrowUpRight, TrendingDown, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AttributeRadar } from "@/components/charts/AttributeRadar";
import { Sparkline } from "@/components/ui/Sparkline";
import { players } from "@/data";
import { cn } from "@/lib/utils";

const posTint: Record<string, string> = {
  GK: "text-warn",
  DF: "text-lime",
  MF: "text-accent",
  FW: "text-pos",
};

export function PlayerDetailPanel() {
  const [activeId, setActiveId] = useState(players[0].id);
  const player = players.find((p) => p.id === activeId) ?? players[0];
  const up = player.ratingDelta >= 0;

  const stats = [
    { label: "Goals", value: player.goals },
    { label: "Assists", value: player.assists },
    { label: "xG", value: player.xg.toFixed(1) },
    { label: "Minutes", value: player.minutes.toLocaleString() },
  ];

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Player Model</CardTitle>
        <Badge variant="neutral">Squad · 6</Badge>
      </CardHeader>
      <CardContent>
        {/* Roster selector */}
        <div className="mask-fade-x -mx-1 flex gap-2 overflow-x-auto px-1 pb-3">
          {players.map((p) => (
            <button
              key={p.id}
              onClick={() => setActiveId(p.id)}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-lg border px-2.5 py-1.5 text-xs transition-colors",
                p.id === activeId
                  ? "border-accent/30 bg-accent/10 text-ink"
                  : "border-line bg-surface-2/60 text-muted hover:border-line-strong hover:text-ink",
              )}
            >
              <span className="font-mono text-[10px] text-faint">
                {p.number}
              </span>
              {p.name.split(" ")[1]}
            </button>
          ))}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {/* Identity + radar */}
          <div>
            <div className="flex items-center gap-3">
              <span className="grid h-12 w-12 place-items-center rounded-xl border border-line bg-gradient-to-br from-surface-2 to-base font-mono text-lg font-semibold text-ink">
                {player.number}
              </span>
              <div>
                <p className="text-sm font-semibold text-ink">{player.name}</p>
                <p className="flex items-center gap-1.5 text-xs text-muted">
                  <span className={cn("font-medium", posTint[player.position])}>
                    {player.position}
                  </span>
                  · {player.club}
                </p>
              </div>
            </div>

            <div className="mt-3 flex items-end gap-3">
              <div>
                <p className="text-[11px] text-faint">Model rating</p>
                <p className="font-mono text-3xl font-semibold tracking-tight text-ink">
                  {player.rating.toFixed(1)}
                </p>
              </div>
              <span
                className={cn(
                  "mb-1 inline-flex items-center gap-0.5 text-xs font-medium",
                  up ? "text-pos" : "text-neg",
                )}
              >
                {up ? (
                  <TrendingUp className="h-3.5 w-3.5" />
                ) : (
                  <TrendingDown className="h-3.5 w-3.5" />
                )}
                {up ? "+" : "−"}
                {Math.abs(player.ratingDelta).toFixed(1)}
              </span>
            </div>

            <div className="mt-3">
              <div className="mb-1 flex items-center justify-between text-[11px] text-faint">
                <span>Form (12 matches)</span>
                <span className="tnum text-muted">{player.form}% conf.</span>
              </div>
              <Sparkline
                data={player.formCurve}
                width={260}
                height={44}
                className="w-full"
              />
            </div>
          </div>

          {/* Radar */}
          <div className="h-[220px] sm:h-auto">
            <motion.div
              key={player.id}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              className="h-full min-h-[200px]"
            >
              <AttributeRadar attributes={player.attributes} />
            </motion.div>
          </div>
        </div>

        {/* Stat strip */}
        <div className="mt-4 grid grid-cols-4 gap-px overflow-hidden rounded-xl border border-line bg-line">
          {stats.map((s) => (
            <div key={s.label} className="bg-surface px-3 py-2.5 text-center">
              <p className="tnum font-mono text-base font-semibold text-ink">
                {s.value}
              </p>
              <p className="mt-0.5 text-[10px] uppercase tracking-wide text-faint">
                {s.label}
              </p>
            </div>
          ))}
        </div>

        <button className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-lg border border-line bg-surface-2/60 py-2 text-xs font-medium text-muted transition-colors hover:border-line-strong hover:text-ink">
          Open full player report
          <ArrowUpRight className="h-3.5 w-3.5" />
        </button>
      </CardContent>
    </Card>
  );
}
