export type Trend = "up" | "down" | "flat";

export interface SparkPoint {
  x: number;
  v: number;
}

export interface Kpi {
  id: string;
  label: string;
  /** Pre-formatted display value, e.g. "68.4%". */
  value: string;
  /** Raw numeric value for count-up animation. */
  raw: number;
  /** Suffix appended after the animated value (e.g. "%", "k"). */
  suffix?: string;
  prefix?: string;
  decimals?: number;
  delta: number;
  deltaLabel: string;
  trend: Trend;
  /** Higher-is-better metric? Controls delta color. */
  positiveIsGood?: boolean;
  spark: SparkPoint[];
  hint: string;
}

export interface PerfPoint {
  matchweek: string;
  xg: number;
  xga: number;
  ppda: number;
  points: number;
}

export interface PlayerAttributes {
  pace: number;
  shooting: number;
  passing: number;
  dribbling: number;
  defending: number;
  physical: number;
}

export interface Player {
  id: string;
  name: string;
  position: "GK" | "DF" | "MF" | "FW";
  club: string;
  number: number;
  rating: number;
  ratingDelta: number;
  goals: number;
  assists: number;
  xg: number;
  minutes: number;
  /** 0–100 model confidence on availability / form. */
  form: number;
  attributes: PlayerAttributes;
  formCurve: SparkPoint[];
}

export interface TeamStanding {
  id: string;
  rank: number;
  club: string;
  short: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  xgDiff: number;
  points: number;
  winProb: number;
  form: ("W" | "D" | "L")[];
}

export interface MatchInsight {
  id: string;
  fixture: string;
  competition: string;
  kickoff: string;
  homeWin: number;
  draw: number;
  awayWin: number;
  projectedScore: string;
  edge: string;
}

export interface Insight {
  id: string;
  kind: "model" | "alert" | "scouting" | "fitness";
  title: string;
  detail: string;
  time: string;
  metric?: string;
}
