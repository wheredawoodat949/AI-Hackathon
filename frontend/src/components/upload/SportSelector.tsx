import { motion } from "motion/react";
import { Check } from "lucide-react";
import { sports, type SportId } from "@/data/sports";
import { cn } from "@/lib/utils";

interface SportSelectorProps {
  value: SportId;
  onChange: (id: SportId) => void;
}

export function SportSelector({ value, onChange }: SportSelectorProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Select sport"
      className="grid grid-cols-1 gap-3 sm:grid-cols-3"
    >
      {sports.map((sport, i) => {
        const active = sport.id === value;
        return (
          <motion.button
            key={sport.id}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(sport.id)}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: i * 0.06, ease: [0.22, 1, 0.36, 1] }}
            className={cn(
              "group relative overflow-hidden rounded-2xl border p-5 text-left transition-colors",
              active
                ? "border-accent/40 bg-accent/[0.06]"
                : "border-line bg-surface/60 hover:border-line-strong hover:bg-surface-2/60",
            )}
          >
            {active && (
              <span className="absolute right-3 top-3 grid h-5 w-5 place-items-center rounded-full bg-accent text-base">
                <Check className="h-3 w-3" strokeWidth={3} />
              </span>
            )}
            <span
              className={cn(
                "grid h-11 w-11 place-items-center rounded-xl border transition-colors",
                active
                  ? "border-accent/30 bg-accent/10 text-accent"
                  : "border-line bg-surface-2 text-muted group-hover:text-ink",
              )}
            >
              <sport.icon className="h-5 w-5" />
            </span>
            <p className="mt-3 text-sm font-semibold text-ink">{sport.name}</p>
            <p className="mt-0.5 text-xs text-muted">{sport.blurb}</p>
          </motion.button>
        );
      })}
    </div>
  );
}
