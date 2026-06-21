import { cn } from "@/lib/utils";

/**
 * Ambient background layer: dot grid + slow-drifting green radial glow + grain.
 * Purely decorative, sits behind content. `animate` toggles the slow drift.
 */
export function Ambient({
  className,
  glow = true,
  grid = "dot",
  animate = true,
}: {
  className?: string;
  glow?: boolean;
  grid?: "dot" | "line" | "none";
  animate?: boolean;
}) {
  return (
    <div
      aria-hidden="true"
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
    >
      {grid !== "none" && (
        <>
          <div
            className={cn(
              "absolute inset-0 mask-fade-b opacity-70",
              grid === "dot" ? "bg-dot-grid" : "bg-line-grid",
            )}
          />
          {/* Apex flow: lime-tinted dot grid that drifts + gradients in and out.
              Outer layer pulses opacity, inner layer drifts the dots. */}
          <div
            className={cn(
              "mask-radial-soft absolute inset-0",
              animate && "motion-safe:animate-dot-pulse",
            )}
          >
            <div
              className={cn(
                "bg-dot-grid-accent absolute inset-0",
                animate && "motion-safe:animate-dot-drift",
              )}
            />
          </div>
        </>
      )}

      {glow && (
        <>
          <div
            className={cn(
              "absolute -top-40 left-1/2 h-[520px] w-[820px] -translate-x-1/2 rounded-full",
              "bg-[radial-gradient(ellipse_at_center,rgba(194,242,74,0.16),transparent_62%)] blur-[40px]",
              animate && "motion-safe:animate-glow-drift",
            )}
          />
          <div className="absolute -bottom-48 right-[-10%] h-[440px] w-[600px] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(16,185,129,0.1),transparent_65%)] blur-[60px]" />
        </>
      )}

      <div className="absolute inset-0 noise-overlay opacity-[0.035] mix-blend-soft-light" />
    </div>
  );
}
