import {
  Activity,
  Brain,
  Radar,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import { motion } from "motion/react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useAppData } from "@/store/appData";
import type { Insight } from "@/data/types";

const config: Record<
  Insight["kind"],
  { icon: LucideIcon; tint: string; label: string }
> = {
  model: { icon: Brain, tint: "text-accent", label: "Model" },
  scouting: { icon: Radar, tint: "text-lime", label: "Scouting" },
  fitness: { icon: Activity, tint: "text-warn", label: "Fitness" },
  alert: { icon: TriangleAlert, tint: "text-neg", label: "Alert" },
};

export function InsightsFeed() {
  const { insights } = useAppData();
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Insight Feed</CardTitle>
        <Badge variant="accent">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
          Live
        </Badge>
      </CardHeader>
      <CardContent className="px-0 pb-2">
        <ul className="flex flex-col">
          {insights.slice(0, 6).map((item, i) => {
            const c = config[item.kind];
            return (
              <motion.li
                key={item.id}
                initial={{ opacity: 0, x: -8 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06 }}
                className="flex gap-3 border-t border-line/60 px-5 py-3.5 transition-colors first:border-t-0 hover:bg-white/[0.02]"
              >
                <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-line bg-surface-2">
                  <c.icon className={`h-4 w-4 ${c.tint}`} />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-medium text-ink">
                      {item.title}
                    </p>
                    {item.metric && (
                      <span className="tnum shrink-0 font-mono text-xs text-accent">
                        {item.metric}
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-xs leading-relaxed text-muted">
                    {item.detail}
                  </p>
                  <div className="mt-1.5 flex items-center gap-2 text-[11px] text-faint">
                    <span className="uppercase tracking-wide">{c.label}</span>
                    <span className="h-0.5 w-0.5 rounded-full bg-faint" />
                    <span>{item.time}</span>
                  </div>
                </div>
              </motion.li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
