import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import type { PlayerAttributes } from "@/data/types";
import { chart } from "./chartTheme";

const labels: Record<keyof PlayerAttributes, string> = {
  pace: "Pace",
  shooting: "Shooting",
  passing: "Passing",
  dribbling: "Dribbling",
  defending: "Defending",
  physical: "Physical",
};

export function AttributeRadar({ attributes }: { attributes: PlayerAttributes }) {
  const data = (Object.keys(labels) as (keyof PlayerAttributes)[]).map((k) => ({
    attribute: labels[k],
    value: attributes[k],
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke={chart.grid} />
        <PolarAngleAxis
          dataKey="attribute"
          tick={{ fill: chart.tick, fontSize: 11 }}
        />
        <Radar
          dataKey="value"
          stroke={chart.accent}
          strokeWidth={2}
          fill={chart.accent}
          fillOpacity={0.18}
          dot={{ r: 2.5, fill: chart.accent }}
          isAnimationActive
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
