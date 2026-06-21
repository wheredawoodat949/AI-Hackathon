import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function CTA() {
  return (
    <section className="relative py-24">
      <div className="mx-auto max-w-4xl px-4">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="relative overflow-hidden rounded-3xl border border-line-strong bg-panel px-6 py-16 text-center"
        >
          <div className="pointer-events-none absolute inset-x-0 -top-24 mx-auto h-64 w-[80%] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(194,242,74,0.18),transparent_70%)] blur-2xl" />
          <div className="bg-dot-grid pointer-events-none absolute inset-0 opacity-40" />

          <div className="relative">
            <h2 className="text-balance text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
              See your next match through the model.
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-pretty text-muted">
              Spin up a workspace with live sample data in under a minute. No
              setup, no integrations required to explore.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link to="/app">
                <Button size="lg">
                  Launch the platform
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Button size="lg" variant="secondary">
                Talk to our team
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
