import { motion } from "motion/react";
import { AnimatedNumber } from "@/components/ui/AnimatedNumber";
import { Ambient } from "@/components/ui/Ambient";
import { landingStats } from "@/data";

export function StatsBand() {
  return (
    <section id="metrics" className="relative py-24">
      <div className="mx-auto max-w-6xl px-4">
        <div className="relative overflow-hidden rounded-3xl border border-line bg-panel/60 px-6 py-12 md:px-12">
          <Ambient grid="line" glow animate className="opacity-80" />

          <div className="relative grid grid-cols-2 gap-y-10 lg:grid-cols-4">
            {landingStats.map((s, i) => (
              <motion.div
                key={s.id}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className="relative px-2 text-center"
              >
                <p className="text-gradient-accent font-mono text-4xl font-semibold tracking-tight sm:text-5xl">
                  <AnimatedNumber
                    value={s.value}
                    decimals={s.decimals}
                    suffix={s.suffix}
                  />
                </p>
                <p className="mt-2 text-sm text-muted">{s.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
