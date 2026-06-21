import { motion } from "motion/react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Step {
  id: string;
  label: string;
}

interface StepIndicatorProps {
  steps: Step[];
  current: number;
}

export function StepIndicator({ steps, current }: StepIndicatorProps) {
  return (
    <ol className="flex items-center gap-2 sm:gap-3">
      {steps.map((step, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <li key={step.id} className="flex flex-1 items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2.5">
              <span
                className={cn(
                  "grid h-7 w-7 shrink-0 place-items-center rounded-full border text-xs font-medium transition-colors",
                  done && "border-accent/40 bg-accent/15 text-accent",
                  active && "border-accent bg-accent text-base",
                  !done && !active && "border-line bg-surface-2 text-faint",
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" strokeWidth={3} /> : i + 1}
              </span>
              <span
                className={cn(
                  "hidden text-xs font-medium transition-colors sm:block",
                  active ? "text-ink" : done ? "text-muted" : "text-faint",
                )}
              >
                {step.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className="relative h-px flex-1 bg-line">
                <motion.div
                  className="absolute inset-y-0 left-0 bg-accent/50"
                  initial={false}
                  animate={{ width: done ? "100%" : "0%" }}
                  transition={{ duration: 0.4 }}
                />
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );
}
