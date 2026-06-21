/** Shared chart palette + primitives so every chart matches the dark theme. */
export const chart = {
  accent: "#c2f24a",
  emerald: "#84cc16",
  lime: "#a3e635",
  neg: "#f87171",
  grid: "rgba(255,255,255,0.06)",
  axis: "rgba(255,255,255,0.28)",
  tick: "#8b938f",
  surface: "#101315",
  line: "rgba(255,255,255,0.1)",
} as const;

export const axisProps = {
  stroke: "transparent",
  tick: { fill: chart.tick, fontSize: 11 },
  tickLine: false,
  axisLine: false,
} as const;
