import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Variant = "neutral" | "accent" | "positive" | "negative" | "warning";

const variants: Record<Variant, string> = {
  neutral: "border-line-strong bg-white/[0.03] text-muted",
  accent: "border-accent/25 bg-accent/10 text-accent",
  positive: "border-pos/25 bg-pos/10 text-pos",
  negative: "border-neg/25 bg-neg/10 text-neg",
  warning: "border-warn/25 bg-warn/10 text-warn",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

export function Badge({
  variant = "neutral",
  className,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5",
        "text-[11px] font-medium tracking-wide",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
