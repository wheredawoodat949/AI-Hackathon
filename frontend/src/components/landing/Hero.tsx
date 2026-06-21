import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, CirclePlay, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Ambient } from "@/components/ui/Ambient";
import { ProductPreview } from "./ProductPreview";

const ease = [0.22, 1, 0.36, 1] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, delay: 0.1 + i * 0.08, ease },
  }),
};

export function Hero() {
  return (
    <section className="relative overflow-hidden pt-36 pb-20 md:pt-44">
      <Ambient grid="dot" glow animate />

      <div className="relative mx-auto max-w-6xl px-4">
        <div className="mx-auto max-w-3xl text-center">
          <motion.a
            href="#features"
            custom={0}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="inline-flex items-center gap-2 rounded-full border border-line bg-surface/60 py-1 pl-1.5 pr-3 text-xs text-muted backdrop-blur-sm transition-colors hover:border-line-strong"
          >
            <span className="inline-flex items-center gap-1 rounded-full border border-accent/25 bg-accent/10 px-2 py-0.5 text-[10px] font-medium text-accent">
              <Sparkles className="h-3 w-3" /> New
            </span>
            Real-time win-probability, now live
            <ArrowRight className="h-3 w-3" />
          </motion.a>

          <motion.h1
            custom={1}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="mt-6 text-balance text-4xl font-semibold leading-[1.05] tracking-tight text-ink sm:text-5xl md:text-6xl"
          >
            Performance intelligence for{" "}
            <span className="text-gradient-accent">elite football</span>.
          </motion.h1>

          <motion.p
            custom={2}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="mx-auto mt-5 max-w-xl text-pretty text-base leading-relaxed text-muted sm:text-lg"
          >
            MotionCast turns raw event, tracking, and biometric data into the
            decisions that win matches — player models, opponent breakdowns, and
            win-probability you can act on before kickoff.
          </motion.p>

          <motion.div
            custom={3}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row"
          >
            <Link to="/app">
              <Button size="lg">
                Launch the platform
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Button size="lg" variant="secondary">
              <CirclePlay className="h-4 w-4" />
              Watch 2-min demo
            </Button>
          </motion.div>

          <motion.p
            custom={4}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            className="mt-5 text-xs text-faint"
          >
            Trusted by 142 clubs & federations · SOC 2 Type II · 99.98% uptime
          </motion.p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.5, ease }}
          className="mt-16 [perspective:2000px]"
        >
          <div className="mask-fade-b">
            <ProductPreview />
          </div>
        </motion.div>
      </div>
    </section>
  );
}
