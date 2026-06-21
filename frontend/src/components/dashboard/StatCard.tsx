import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { motion } from "motion/react";
import { Card } from "@/components/ui/Card";
import { Sparkline } from "@/components/ui/Sparkline";
import { AnimatedNumber } from "@/components/ui/AnimatedNumber";
import type { Kpi } from "@/data/types";
import { cn } from "@/lib/utils";

const TrendIcon = {
  up: ArrowUpRight,
  down: ArrowDownRight,
  flat: Minus,
} as const;

export function StatCard({ kpi, index = 0 }: { kpi: Kpi; index?: number }) {
  const Icon = TrendIcon[kpi.trend];

  // For "lower is better" metrics a down trend is still good.
  const good =
    kpi.delta === 0
      ? "flat"
      : (kpi.delta > 0) === (kpi.positiveIsGood ?? true)
        ? "good"
        : "bad";

  const deltaColor =
    good === "good"
      ? "text-pos"
      : good === "bad"
        ? "text-neg"
        : "text-muted";

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, delay: index * 0.06, ease: [0.22, 1, 0.36, 1] }}
    >
      <Card className="group h-full p-5 transition-colors hover:border-line-strong">
        <div className="flex items-start justify-between">
          <div className="flex flex-col gap-1">
            <p className="text-xs font-medium text-muted">{kpi.label}</p>
            <div className="flex items-baseline gap-1">
              <span className="font-mono text-2xl font-semibold tracking-tight text-ink">
                {kpi.prefix}
                <AnimatedNumber
                  value={kpi.raw}
                  decimals={kpi.decimals ?? 0}
                  suffix={kpi.suffix}
                />
              </span>
            </div>
          </div>
          <Sparkline
            data={kpi.spark}
            width={92}
            height={40}
            stroke={good === "bad" ? "var(--color-neg)" : "var(--color-accent)"}
          />
        </div>

        <div className="mt-4 flex items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-0.5 text-xs font-medium",
              deltaColor,
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {kpi.deltaLabel}
          </span>
        </div>

        <p className="mt-2 text-[11px] leading-relaxed text-faint">{kpi.hint}</p>
      </Card>
    </motion.div>
  );
}
