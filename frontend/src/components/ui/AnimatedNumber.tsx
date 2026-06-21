import { useRef } from "react";
import { useInView } from "motion/react";
import { useCountUp } from "@/hooks/useCountUp";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

interface AnimatedNumberProps {
  value: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  duration?: number;
  className?: string;
  /** Force-run without waiting to scroll into view. */
  eager?: boolean;
}

/** Number that counts up the first time it scrolls into view. */
export function AnimatedNumber({
  value,
  decimals = 0,
  prefix,
  suffix,
  duration,
  className,
  eager = false,
}: AnimatedNumberProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.6 });
  const current = useCountUp(value, {
    decimals,
    duration,
    active: eager || inView,
  });

  return (
    <span ref={ref} className={cn("tnum", className)}>
      {prefix}
      {formatNumber(current, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </span>
  );
}
