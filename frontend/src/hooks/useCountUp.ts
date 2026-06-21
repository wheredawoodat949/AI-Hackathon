import { useEffect, useRef, useState } from "react";

interface CountUpOptions {
  /** Animation duration in ms. */
  duration?: number;
  /** Whether the animation should run. Pass an in-view flag here. */
  active?: boolean;
  /** Decimal places to round to. */
  decimals?: number;
}

const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// easeOutExpo — fast then settles, feels precise rather than bouncy.
const ease = (t: number) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t));

/** Animate a number from 0 → target once `active` becomes true. */
export function useCountUp(
  target: number,
  { duration = 1400, active = true, decimals = 0 }: CountUpOptions = {},
): number {
  const [value, setValue] = useState(0);
  const frame = useRef<number>(0);
  const done = useRef(false);

  useEffect(() => {
    if (!active || done.current) return;

    if (prefersReducedMotion()) {
      done.current = true;
      const id = requestAnimationFrame(() => setValue(target));
      return () => cancelAnimationFrame(id);
    }

    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const factor = Math.pow(10, decimals);
      setValue(Math.round(target * ease(progress) * factor) / factor);
      if (progress < 1) {
        frame.current = requestAnimationFrame(tick);
      } else {
        done.current = true;
      }
    };
    frame.current = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(frame.current);
  }, [target, duration, active, decimals]);

  return value;
}
