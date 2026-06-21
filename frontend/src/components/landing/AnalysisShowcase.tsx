import { motion } from "motion/react";
import {
  Crosshair,
  Gauge,
  ScanLine,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";
import { Ambient } from "@/components/ui/Ambient";
import { SectionHeading } from "./SectionHeading";

const ease = [0.22, 1, 0.36, 1] as const;

const insights = [
  {
    icon: ScanLine,
    title: "Player detection",
    value: "22 / 22 tracked",
    detail: "Per-frame bounding boxes locked across both teams.",
  },
  {
    icon: Crosshair,
    title: "Ball trajectory",
    value: "98.4% continuity",
    detail: "Optical tracking holds through occlusion and congestion.",
  },
  {
    icon: Target,
    title: "Chance quality",
    value: "0.62 xG · shot 41:08",
    detail: "Auto-flagged high-value moment with the clip attached.",
  },
];

export function AnalysisShowcase() {
  return (
    <section id="showcase" className="relative overflow-hidden py-24">
      <Ambient grid="dot" glow animate className="opacity-50" />

      <div className="relative mx-auto max-w-6xl px-4">
        <SectionHeading
          eyebrow="See it in action"
          title="Computer vision on raw game film"
          description="Drop in match footage and MotionCast turns it into tracked players, ball trajectory, and calibrated metrics — every number linked back to the exact frame that produced it."
        />

        <div className="mt-14 grid gap-4 lg:grid-cols-3">
          {/* Framed player with analysis HUD */}
          <motion.div
            initial={{ opacity: 0, y: 28 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.7, ease }}
            className="lg:col-span-2"
          >
            <div className="relative rounded-2xl border border-line-strong bg-panel/80 p-1.5 shadow-glow backdrop-blur-xl">
              {/* window chrome */}
              <div className="flex items-center gap-2 px-3 py-2">
                <span className="flex gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
                  <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
                  <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
                </span>
                <div className="mx-auto flex items-center gap-2 rounded-md border border-line bg-base/60 px-3 py-1 font-mono text-[10px] text-faint">
                  motioncast.io/film/halston-city-vs-riverside
                </div>
              </div>

              <div className="relative aspect-video overflow-hidden rounded-xl border border-line bg-black">
                <video
                  src="/soccer-demo.mp4"
                  autoPlay
                  muted
                  loop
                  playsInline
                  controls
                  className="h-full w-full bg-black object-cover"
                />

                {/* scrim so overlays stay legible */}
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/55 via-transparent to-black/30" />

                {/* "AI detected" pulse tag */}
                <motion.div
                  initial={{ opacity: 0, x: -12 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.4, ease }}
                  className="pointer-events-none absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-md border border-accent/30 bg-base/70 px-2 py-1 font-mono text-[10px] font-medium text-accent backdrop-blur-sm"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-accent motion-safe:animate-ping" />
                  AI · LIVE TRACKING
                </motion.div>

                {/* simulated detection boxes */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.7, ease }}
                  className="pointer-events-none absolute left-[24%] top-[40%] h-20 w-12 rounded-md border-2 border-accent/80 shadow-[0_0_20px_-4px_rgba(194,242,74,0.6)]"
                >
                  <span className="absolute -top-4 left-0 rounded-sm bg-accent px-1 font-mono text-[9px] font-semibold text-base">
                    #7 · 0.94
                  </span>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.9, ease }}
                  className="pointer-events-none absolute right-[30%] top-[52%] h-16 w-10 rounded-md border-2 border-white/70"
                >
                  <span className="absolute -top-4 left-0 rounded-sm bg-white/90 px-1 font-mono text-[9px] font-semibold text-base">
                    GK · 0.88
                  </span>
                </motion.div>

                {/* HUD metric chips */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.55, ease }}
                  className="pointer-events-none absolute right-3 top-3 flex flex-col items-end gap-1.5"
                >
                  <span className="inline-flex items-center gap-1.5 rounded-md border border-line bg-base/70 px-2 py-1 font-mono text-[10px] text-ink backdrop-blur-sm">
                    <Gauge className="h-3 w-3 text-accent" /> Possession 57%
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-md border border-line bg-base/70 px-2 py-1 font-mono text-[10px] text-ink backdrop-blur-sm">
                    <Target className="h-3 w-3 text-accent" /> xG 1.84
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-md border border-line bg-base/70 px-2 py-1 font-mono text-[10px] text-ink backdrop-blur-sm">
                    <Zap className="h-3 w-3 text-accent" /> 34.1 km/h
                  </span>
                </motion.div>

                {/* bottom possession bar */}
                <div className="pointer-events-none absolute inset-x-3 bottom-3">
                  <div className="flex items-center justify-between font-mono text-[10px] text-ink">
                    <span>Halston City</span>
                    <span className="text-faint">Possession</span>
                    <span>Riverside</span>
                  </div>
                  <div className="mt-1 flex h-1.5 overflow-hidden rounded-full bg-white/10">
                    <motion.span
                      className="block h-full bg-accent"
                      initial={{ width: "0%" }}
                      whileInView={{ width: "57%" }}
                      viewport={{ once: true }}
                      transition={{ duration: 1.1, delay: 0.5, ease }}
                    />
                    <span className="block h-full flex-1 bg-white/25" />
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Live insight callouts */}
          <div className="flex flex-col gap-3">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6, ease }}
              className="inline-flex items-center gap-2 self-start rounded-full border border-accent/25 bg-accent/10 px-3 py-1 text-[11px] font-medium text-accent"
            >
              <Sparkles className="h-3 w-3" /> Auto-generated insights
            </motion.div>

            {insights.map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.55, delay: 0.1 + i * 0.1, ease }}
                className="group relative overflow-hidden rounded-2xl border border-line bg-surface/50 p-4 transition-colors hover:border-line-strong"
              >
                <div className="flex items-start gap-3">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-line bg-surface-2 text-accent transition-colors group-hover:border-accent/30">
                    <item.icon className="h-4 w-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-ink">{item.title}</p>
                    <p className="mt-0.5 font-mono text-sm font-semibold text-accent">
                      {item.value}
                    </p>
                    <p className="mt-1 text-xs leading-relaxed text-muted">
                      {item.detail}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
