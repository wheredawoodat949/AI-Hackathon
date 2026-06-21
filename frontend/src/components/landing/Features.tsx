import {
  Activity,
  Brain,
  Gauge,
  LineChart,
  Radar,
  Video,
  type LucideIcon,
} from "lucide-react";
import { motion } from "motion/react";
import { Sparkline } from "@/components/ui/Sparkline";
import { kpis } from "@/data";
import { cn } from "@/lib/utils";
import { SectionHeading } from "./SectionHeading";

interface Feature {
  icon: LucideIcon;
  title: string;
  body: string;
  span?: string;
  accent?: boolean;
}

const features: Feature[] = [
  {
    icon: Gauge,
    title: "Win-probability engine",
    body: "A calibrated model recomputes match outcome odds in real time as lineups, form, and load signals change — so you adjust before kickoff.",
    span: "lg:col-span-2",
    accent: true,
  },
  {
    icon: Brain,
    title: "Player performance models",
    body: "Per-90 attribute models, finishing sustainability, and form curves for every athlete in your squad.",
  },
  {
    icon: Radar,
    title: "Opponent scouting",
    body: "Auto-detected shape changes, press triggers, and set-piece tendencies from the latest fixtures.",
  },
  {
    icon: Video,
    title: "Film room",
    body: "Every model insight is one click from the tagged clip that produced it.",
  },
  {
    icon: Activity,
    title: "Fitness & load",
    body: "High-speed running and acute:chronic workload tracking with managed-minutes recommendations.",
    span: "lg:col-span-2",
  },
];

export function Features() {
  return (
    <section id="features" className="relative py-24">
      <div className="mx-auto max-w-6xl px-4">
        <SectionHeading
          eyebrow="The platform"
          title="One model of truth, end to end"
          description="From the raw tracking feed to the decision on the touchline, MotionCast unifies every layer of football analysis into a single, fast workspace."
        />

        <div className="mt-14 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.55, delay: i * 0.06, ease: [0.22, 1, 0.36, 1] }}
              className={cn(
                "group relative overflow-hidden rounded-2xl border border-line bg-surface/50 p-6 transition-colors hover:border-line-strong",
                f.span,
              )}
            >
              {f.accent && (
                <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-[radial-gradient(circle,rgba(194,242,74,0.12),transparent_70%)]" />
              )}
              <div className="relative">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-surface-2 text-accent transition-colors group-hover:border-accent/30">
                  <f.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-base font-semibold text-ink">
                  {f.title}
                </h3>
                <p className="mt-2 max-w-md text-sm leading-relaxed text-muted">
                  {f.body}
                </p>

                {f.accent && (
                  <div className="mt-6 flex items-end gap-6 rounded-xl border border-line bg-base/60 p-4">
                    <div>
                      <p className="text-[11px] text-faint">Next fixture</p>
                      <p className="font-mono text-3xl font-semibold text-ink">
                        71.2<span className="text-lg text-muted">%</span>
                      </p>
                      <p className="mt-0.5 text-[11px] text-pos">
                        +4.8 pts last 5
                      </p>
                    </div>
                    <Sparkline
                      data={kpis[0].spark}
                      width={200}
                      height={56}
                      className="flex-1"
                    />
                  </div>
                )}
              </div>
            </motion.div>
          ))}

          {/* trailing stat card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.55, delay: 0.3 }}
            className="relative flex flex-col justify-between overflow-hidden rounded-2xl border border-line bg-gradient-to-br from-surface/60 to-base p-6"
          >
            <LineChart className="h-5 w-5 text-accent" />
            <div>
              <p className="font-mono text-3xl font-semibold text-ink">38ms</p>
              <p className="mt-1 text-sm text-muted">
                Median inference latency across 2.4B modeled events.
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
