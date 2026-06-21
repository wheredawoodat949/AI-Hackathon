import { motion } from "motion/react";
import { ArrowRight, Cpu, Database, Target } from "lucide-react";
import { SectionHeading } from "./SectionHeading";

const steps = [
  {
    icon: Database,
    tag: "01 · Ingest",
    title: "Every feed, unified",
    body: "Optical tracking, event data, GPS vests, and medical reports stream into one normalized model within seconds of full-time.",
  },
  {
    icon: Cpu,
    tag: "02 · Model",
    title: "Calibrated, not guessed",
    body: "Position-aware models score chance quality, player form, and outcome probability — back-tested across millions of possessions.",
  },
  {
    icon: Target,
    tag: "03 · Decide",
    title: "Insight on the touchline",
    body: "Coaches get ranked, explainable recommendations linked to the exact clips and numbers behind every call.",
  },
];

export function Workflow() {
  return (
    <section id="platform" className="relative py-24">
      <div className="mx-auto max-w-6xl px-4">
        <SectionHeading
          eyebrow="How it works"
          title="From raw signal to match-day call"
          description="A single pipeline that turns the noise of modern football data into the three or four decisions that actually move a result."
        />

        <div className="relative mt-14 grid gap-4 md:grid-cols-3">
          {steps.map((s, i) => (
            <motion.div
              key={s.tag}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.55, delay: i * 0.1 }}
              className="relative rounded-2xl border border-line bg-surface/50 p-6"
            >
              <div className="flex items-center justify-between">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-surface-2 text-accent">
                  <s.icon className="h-5 w-5" />
                </span>
                {i < steps.length - 1 && (
                  <ArrowRight className="hidden h-4 w-4 text-faint md:block" />
                )}
              </div>
              <p className="mt-4 font-mono text-[11px] uppercase tracking-wider text-accent">
                {s.tag}
              </p>
              <h3 className="mt-1 text-base font-semibold text-ink">
                {s.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
