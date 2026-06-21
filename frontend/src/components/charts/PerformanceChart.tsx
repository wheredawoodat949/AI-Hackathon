import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PerfPoint } from "@/data/types";
import { axisProps, chart } from "./chartTheme";
import { ChartTooltip } from "./ChartTooltip";

export function PerformanceChart({ data }: { data: PerfPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="grad-xg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={chart.accent} stopOpacity={0.35} />
            <stop offset="100%" stopColor={chart.accent} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="grad-xga" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={chart.neg} stopOpacity={0.22} />
            <stop offset="100%" stopColor={chart.neg} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid
          stroke={chart.grid}
          strokeDasharray="3 3"
          vertical={false}
        />
        <XAxis dataKey="matchweek" {...axisProps} interval="preserveStartEnd" />
        <YAxis {...axisProps} width={40} />
        <Tooltip
          content={<ChartTooltip />}
          cursor={{ stroke: chart.line, strokeWidth: 1 }}
        />
        <Area
          type="monotone"
          name="xG"
          dataKey="xg"
          stroke={chart.accent}
          strokeWidth={2}
          fill="url(#grad-xg)"
          dot={false}
          activeDot={{ r: 4, fill: chart.accent, stroke: chart.surface, strokeWidth: 2 }}
        />
        <Area
          type="monotone"
          name="xGA"
          dataKey="xga"
          stroke={chart.neg}
          strokeWidth={1.75}
          strokeDasharray="4 3"
          fill="url(#grad-xga)"
          dot={false}
          activeDot={{ r: 3.5, fill: chart.neg, stroke: chart.surface, strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
