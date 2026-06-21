import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import {
  Activity,
  Brain,
  Check,
  Crosshair,
  Film,
  LoaderCircle,
  ScanLine,
  type LucideIcon,
} from "lucide-react";
import { sportById, type SportId } from "@/data/sports";
import { cn } from "@/lib/utils";

interface Stage {
  icon: LucideIcon;
  label: string;
  detail: string;
}

const STAGES: Stage[] = [
  { icon: Film, label: "Ingesting frames", detail: "Decoding clip · 60 fps" },
  { icon: ScanLine, label: "Detecting players", detail: "22 tracks locked" },
  { icon: Crosshair, label: "Tracking ball trajectory", detail: "Optical flow" },
  { icon: Activity, label: "Computing possession & xG", detail: "Event model" },
  { icon: Brain, label: "Generating insights", detail: "Ranking moments" },
];

interface AnalysisLoadingProps {
  sport: SportId;
  fileName?: string;
  onComplete: () => void;
}

export function AnalysisLoading({
  sport,
  fileName,
  onComplete,
}: AnalysisLoadingProps) {
  const cfg = sportById(sport);
  const [progress, setProgress] = useState(0);
  const doneRef = useRef(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) return 100;
        // Ease out: large early steps, slowing as it approaches 100 — but
        // a floor keeps it moving so it always finishes in a few seconds.
        const remaining = 100 - p;
        const inc = Math.max(0.6, remaining * 0.05) + Math.random() * 2.2;
        return Math.min(100, p + inc);
      });
    }, 120);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (progress >= 100 && !doneRef.current) {
      doneRef.current = true;
      const t = setTimeout(onComplete, 650);
      return () => clearTimeout(t);
    }
  }, [progress, onComplete]);

  const segment = 100 / STAGES.length;
  const activeIndex = Math.min(
    STAGES.length - 1,
    Math.floor(progress / segment),
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="relative overflow-hidden rounded-2xl border border-line bg-surface/60 px-6 py-10 sm:px-8"
    >
      {/* ambient texture */}
      <div className="bg-dot-grid pointer-events-none absolute inset-0 opacity-40" />
      <div className="pointer-events-none absolute inset-x-0 -top-24 mx-auto h-56 w-[70%] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(194,242,74,0.16),transparent_70%)] blur-2xl" />

      <div className="relative">
        <div className="flex items-center gap-3">
          <span className="relative grid h-11 w-11 place-items-center rounded-xl border border-accent/30 bg-accent/10 text-accent">
            <LoaderCircle className="h-5 w-5 animate-spin" />
            <span className="absolute inset-0 rounded-xl border border-accent/20 motion-safe:animate-ping" />
          </span>
          <div className="min-w-0">
            <h2 className="text-base font-semibold tracking-tight text-ink">
              Analyzing film
            </h2>
            <p className="truncate text-xs text-muted">
              {cfg.name} · {fileName ?? "game film"}
            </p>
          </div>
          <span className="tnum ml-auto font-mono text-2xl font-semibold text-accent">
            {Math.round(progress)}
            <span className="text-base text-muted">%</span>
          </span>
        </div>

        {/* progress bar with shimmer */}
        <div className="relative mt-5 h-2 overflow-hidden rounded-full bg-white/[0.06]">
          <motion.div
            className="relative h-full rounded-full bg-gradient-to-r from-emerald to-accent"
            initial={false}
            animate={{ width: `${progress}%` }}
            transition={{ ease: "easeOut", duration: 0.25 }}
          >
            <span className="absolute inset-0 motion-safe:animate-shimmer bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.45),transparent)]" />
          </motion.div>
        </div>

        {/* stage list */}
        <ul className="mt-6 flex flex-col gap-1.5">
          {STAGES.map((stage, i) => {
            const done = progress >= 100 || i < activeIndex;
            const active = !done && i === activeIndex;
            return (
              <li
                key={stage.label}
                className={cn(
                  "flex items-center gap-3 rounded-lg border px-3 py-2.5 transition-colors",
                  active
                    ? "border-accent/30 bg-accent/[0.06]"
                    : done
                      ? "border-line bg-surface/40"
                      : "border-transparent",
                )}
              >
                <span
                  className={cn(
                    "grid h-7 w-7 shrink-0 place-items-center rounded-lg border transition-colors",
                    done
                      ? "border-accent/40 bg-accent/15 text-accent"
                      : active
                        ? "border-accent/40 bg-accent/10 text-accent"
                        : "border-line bg-surface-2 text-faint",
                  )}
                >
                  {done ? (
                    <Check className="h-3.5 w-3.5" strokeWidth={3} />
                  ) : active ? (
                    <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <stage.icon className="h-3.5 w-3.5" />
                  )}
                </span>
                <span
                  className={cn(
                    "text-sm font-medium transition-colors",
                    done || active ? "text-ink" : "text-faint",
                  )}
                >
                  {stage.label}
                </span>
                <span className="ml-auto font-mono text-[11px] text-faint">
                  {done ? "done" : active ? stage.detail : "queued"}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </motion.div>
  );
}
