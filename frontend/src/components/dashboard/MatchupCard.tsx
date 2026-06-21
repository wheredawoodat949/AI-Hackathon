import { motion } from "motion/react";
import { ChevronRight, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { useAppData } from "@/store/appData";

export function MatchupCard() {
  const { matchups } = useAppData();
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Upcoming Matchups</CardTitle>
        <span className="font-mono text-[11px] text-faint">Win-prob model</span>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {matchups.slice(0, 4).map((m, i) => {
          const [home, away] = m.fixture.split(" vs ");
          return (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06 }}
              className="group rounded-xl border border-line bg-surface-2/50 p-3.5 transition-colors hover:border-line-strong"
            >
              <div className="flex items-center justify-between text-[11px] text-faint">
                <span>{m.competition}</span>
                <span>{m.kickoff}</span>
              </div>

              <div className="mt-1.5 flex items-center justify-between">
                <p className="text-sm font-medium text-ink">
                  {home} <span className="text-faint">vs</span> {away}
                </p>
                <span className="tnum font-mono text-xs text-accent">
                  {m.projectedScore}
                </span>
              </div>

              {/* Win-probability segmented bar */}
              <div className="mt-2.5 flex h-1.5 overflow-hidden rounded-full">
                <span
                  className="bg-accent"
                  style={{ width: `${m.homeWin}%` }}
                  title={`Home ${m.homeWin}%`}
                />
                <span
                  className="bg-white/[0.12]"
                  style={{ width: `${m.draw}%` }}
                  title={`Draw ${m.draw}%`}
                />
                <span
                  className="bg-neg/70"
                  style={{ width: `${m.awayWin}%` }}
                  title={`Away ${m.awayWin}%`}
                />
              </div>
              <div className="mt-1.5 flex items-center justify-between text-[10px] text-faint">
                <span className="tnum text-accent">{m.homeWin}% H</span>
                <span className="tnum">{m.draw}% D</span>
                <span className="tnum text-neg">{m.awayWin}% A</span>
              </div>

              <div className="mt-2.5 flex items-center gap-1.5 border-t border-line/60 pt-2.5 text-[11px] text-muted">
                <Sparkles className="h-3 w-3 text-accent" />
                <span className="flex-1">{m.edge}</span>
                <ChevronRight className="h-3.5 w-3.5 text-faint transition-transform group-hover:translate-x-0.5" />
              </div>
            </motion.div>
          );
        })}
      </CardContent>
    </Card>
  );
}
