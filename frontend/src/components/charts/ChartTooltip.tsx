interface TooltipEntry {
  name?: string | number;
  value?: string | number;
  color?: string;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string | number;
}

/** Dark, glassy tooltip shared across all charts. */
export function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="min-w-[150px] rounded-xl border border-line-strong bg-panel/95 px-3 py-2.5 shadow-card backdrop-blur-md">
      {label != null && (
        <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-faint">
          {label}
        </p>
      )}
      <div className="flex flex-col gap-1">
        {payload.map((entry, i) => (
          <div
            key={i}
            className="flex items-center justify-between gap-4 text-xs"
          >
            <span className="flex items-center gap-1.5 text-muted">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              {entry.name}
            </span>
            <span className="tnum font-medium text-ink">{entry.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
