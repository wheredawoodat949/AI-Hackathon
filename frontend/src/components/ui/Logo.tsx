import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "relative inline-flex h-8 w-8 items-center justify-center rounded-lg",
        "border border-accent/30 bg-accent/10",
        className,
      )}
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path
          d="M8 1.5L14.5 14H1.5L8 1.5Z"
          stroke="var(--color-accent)"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path d="M8 6.5L11 12.5H5L8 6.5Z" fill="var(--color-accent)" />
      </svg>
    </span>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <LogoMark />
      <span className="flex flex-col leading-none">
        <span className="text-[15px] font-semibold tracking-tight text-ink">
          Motion<span className="text-accent">Cast</span>
        </span>
      </span>
    </span>
  );
}
