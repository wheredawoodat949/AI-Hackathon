import type {
  Insight,
  Kpi,
  MatchInsight,
  PerfPoint,
  Player,
  SparkPoint,
  TeamStanding,
} from "./types";

/** Deterministic pseudo-random series so charts look organic but stable. */
function series(seed: number, len: number, base: number, spread: number): SparkPoint[] {
  const out: SparkPoint[] = [];
  let s = seed;
  for (let i = 0; i < len; i++) {
    s = (s * 9301 + 49297) % 233280;
    const r = s / 233280;
    const drift = (i / len) * spread * 0.6;
    out.push({ x: i, v: +(base + drift + (r - 0.5) * spread).toFixed(2) });
  }
  return out;
}

export const kpis: Kpi[] = [
  {
    id: "winprob",
    label: "Win Probability",
    value: "71.2%",
    raw: 71.2,
    suffix: "%",
    decimals: 1,
    delta: 4.8,
    deltaLabel: "+4.8 vs last 5",
    trend: "up",
    positiveIsGood: true,
    spark: series(7, 16, 60, 18),
    hint: "Model-projected probability of winning the next fixture",
  },
  {
    id: "xg",
    label: "Expected Goals / 90",
    value: "2.34",
    raw: 2.34,
    decimals: 2,
    delta: 0.31,
    deltaLabel: "+0.31 xG",
    trend: "up",
    positiveIsGood: true,
    spark: series(21, 16, 1.6, 1.2),
    hint: "Quality-weighted chances created per 90 minutes",
  },
  {
    id: "ppda",
    label: "Pressing Intensity",
    value: "8.7",
    raw: 8.7,
    decimals: 1,
    delta: -1.2,
    deltaLabel: "−1.2 PPDA",
    trend: "down",
    positiveIsGood: true,
    spark: series(44, 16, 11, 4),
    hint: "Passes allowed per defensive action — lower is more aggressive",
  },
  {
    id: "availability",
    label: "Squad Availability",
    value: "92%",
    raw: 92,
    suffix: "%",
    decimals: 0,
    delta: -3,
    deltaLabel: "−3 pts (2 doubts)",
    trend: "down",
    positiveIsGood: true,
    spark: series(63, 16, 90, 10),
    hint: "Share of first-team squad cleared by the fitness model",
  },
];

export const performance: PerfPoint[] = [
  { matchweek: "MW1", xg: 1.4, xga: 1.1, ppda: 11.2, points: 1 },
  { matchweek: "MW2", xg: 2.1, xga: 0.9, ppda: 10.4, points: 4 },
  { matchweek: "MW3", xg: 1.8, xga: 1.4, ppda: 9.8, points: 4 },
  { matchweek: "MW4", xg: 2.6, xga: 0.7, ppda: 9.1, points: 7 },
  { matchweek: "MW5", xg: 2.3, xga: 1.2, ppda: 8.9, points: 10 },
  { matchweek: "MW6", xg: 1.9, xga: 1.6, ppda: 9.4, points: 10 },
  { matchweek: "MW7", xg: 2.8, xga: 0.8, ppda: 8.2, points: 13 },
  { matchweek: "MW8", xg: 3.1, xga: 1.0, ppda: 7.6, points: 16 },
  { matchweek: "MW9", xg: 2.4, xga: 1.3, ppda: 8.7, points: 17 },
  { matchweek: "MW10", xg: 2.9, xga: 0.6, ppda: 7.9, points: 20 },
  { matchweek: "MW11", xg: 2.2, xga: 1.1, ppda: 8.4, points: 23 },
  { matchweek: "MW12", xg: 3.3, xga: 0.9, ppda: 7.1, points: 26 },
];

export const standings: TeamStanding[] = [
  { id: "hal", rank: 1, club: "Halston City", short: "HAL", played: 12, won: 9, drawn: 2, lost: 1, xgDiff: 18.4, points: 29, winProb: 71.2, form: ["W", "W", "D", "W", "W"] },
  { id: "rav", rank: 2, club: "Ravenport United", short: "RAV", played: 12, won: 8, drawn: 3, lost: 1, xgDiff: 14.1, points: 27, winProb: 64.5, form: ["W", "D", "W", "W", "D"] },
  { id: "kgb", rank: 3, club: "Kingsbridge FC", short: "KGB", played: 12, won: 7, drawn: 4, lost: 1, xgDiff: 11.8, points: 25, winProb: 58.9, form: ["D", "W", "W", "D", "W"] },
  { id: "mer", rank: 4, club: "Meridian Athletic", short: "MER", played: 12, won: 7, drawn: 2, lost: 3, xgDiff: 8.2, points: 23, winProb: 52.3, form: ["W", "L", "W", "W", "L"] },
  { id: "ash", rank: 5, club: "Ashford Rovers", short: "ASH", played: 12, won: 6, drawn: 3, lost: 3, xgDiff: 5.6, points: 21, winProb: 47.1, form: ["W", "W", "L", "D", "W"] },
  { id: "nor", rank: 6, club: "Norfield United", short: "NOR", played: 12, won: 5, drawn: 4, lost: 3, xgDiff: 2.1, points: 19, winProb: 41.8, form: ["D", "D", "W", "L", "W"] },
  { id: "car", rank: 7, club: "Carrick Town", short: "CAR", played: 12, won: 5, drawn: 2, lost: 5, xgDiff: -1.4, points: 17, winProb: 35.2, form: ["L", "W", "D", "L", "W"] },
  { id: "sef", rank: 8, club: "Sefton Wanderers", short: "SEF", played: 12, won: 4, drawn: 4, lost: 4, xgDiff: -3.8, points: 16, winProb: 31.6, form: ["D", "L", "W", "D", "L"] },
];

export const players: Player[] = [
  {
    id: "p1",
    name: "Mateo Ferreira",
    position: "FW",
    club: "Halston City",
    number: 9,
    rating: 8.7,
    ratingDelta: 0.4,
    goals: 14,
    assists: 5,
    xg: 11.8,
    minutes: 1042,
    form: 94,
    attributes: { pace: 88, shooting: 92, passing: 74, dribbling: 86, defending: 38, physical: 81 },
    formCurve: series(101, 12, 7.8, 1.6),
  },
  {
    id: "p2",
    name: "Luka Andersson",
    position: "MF",
    club: "Halston City",
    number: 8,
    rating: 8.4,
    ratingDelta: 0.2,
    goals: 6,
    assists: 11,
    xg: 5.2,
    minutes: 1080,
    form: 90,
    attributes: { pace: 76, shooting: 78, passing: 91, dribbling: 84, defending: 70, physical: 79 },
    formCurve: series(202, 12, 7.6, 1.4),
  },
  {
    id: "p3",
    name: "Idris Camara",
    position: "DF",
    club: "Halston City",
    number: 4,
    rating: 8.1,
    ratingDelta: -0.1,
    goals: 2,
    assists: 3,
    xg: 1.4,
    minutes: 1080,
    form: 88,
    attributes: { pace: 82, shooting: 48, passing: 80, dribbling: 66, defending: 90, physical: 88 },
    formCurve: series(303, 12, 7.4, 1.2),
  },
  {
    id: "p4",
    name: "Tobias Vance",
    position: "GK",
    club: "Halston City",
    number: 1,
    rating: 7.9,
    ratingDelta: 0.3,
    goals: 0,
    assists: 1,
    xg: 0,
    minutes: 1080,
    form: 86,
    attributes: { pace: 60, shooting: 22, passing: 74, dribbling: 52, defending: 86, physical: 84 },
    formCurve: series(404, 12, 7.2, 1.0),
  },
  {
    id: "p5",
    name: "Diego Sorrentino",
    position: "FW",
    club: "Halston City",
    number: 11,
    rating: 7.8,
    ratingDelta: 0.5,
    goals: 9,
    assists: 7,
    xg: 8.1,
    minutes: 902,
    form: 91,
    attributes: { pace: 90, shooting: 82, passing: 77, dribbling: 89, defending: 34, physical: 70 },
    formCurve: series(505, 12, 7.3, 1.5),
  },
  {
    id: "p6",
    name: "Noah Bergström",
    position: "MF",
    club: "Halston City",
    number: 6,
    rating: 7.6,
    ratingDelta: 0.1,
    goals: 3,
    assists: 4,
    xg: 2.6,
    minutes: 1015,
    form: 83,
    attributes: { pace: 72, shooting: 66, passing: 86, dribbling: 75, defending: 84, physical: 82 },
    formCurve: series(606, 12, 7.1, 1.1),
  },
];

export const matchInsights: MatchInsight[] = [
  {
    id: "m1",
    fixture: "Halston City vs Ravenport United",
    competition: "Apex Premier · MW13",
    kickoff: "Sat 17:30",
    homeWin: 58,
    draw: 24,
    awayWin: 18,
    projectedScore: "2.1 – 1.2",
    edge: "Press triggers exploit RAV's high line",
  },
  {
    id: "m2",
    fixture: "Kingsbridge FC vs Meridian Athletic",
    competition: "Apex Premier · MW13",
    kickoff: "Sun 14:00",
    homeWin: 47,
    draw: 28,
    awayWin: 25,
    projectedScore: "1.6 – 1.3",
    edge: "Set-piece xG advantage to KGB",
  },
  {
    id: "m3",
    fixture: "Ashford Rovers vs Carrick Town",
    competition: "Apex Cup · R16",
    kickoff: "Wed 19:45",
    homeWin: 51,
    draw: 26,
    awayWin: 23,
    projectedScore: "1.8 – 1.1",
    edge: "Transition speed differential +0.7",
  },
];

export const insights: Insight[] = [
  {
    id: "i1",
    kind: "model",
    title: "Win probability up 4.8 pts",
    detail:
      "Halston City's projected win share vs Ravenport rose after factoring Ferreira's return to full training.",
    time: "12m ago",
    metric: "71.2%",
  },
  {
    id: "i2",
    kind: "scouting",
    title: "Breakout flag: D. Sorrentino",
    detail:
      "Over-performing xG by +2.4 across the last 6 matches. Finishing model rates the run as sustainable.",
    time: "1h ago",
    metric: "+2.4 xG",
  },
  {
    id: "i3",
    kind: "fitness",
    title: "Load alert: I. Camara",
    detail:
      "High-speed running 18% above 4-week baseline. Recommend managed minutes for the midweek cup tie.",
    time: "3h ago",
    metric: "18% ↑",
  },
  {
    id: "i4",
    kind: "alert",
    title: "Opponent shape shift detected",
    detail:
      "Ravenport trialled a 3-4-3 build-out in their last fixture — pressing plan auto-updated.",
    time: "5h ago",
    metric: "3-4-3",
  },
];

export const landingStats = [
  { id: "s1", label: "Events modeled / season", value: 2.4, suffix: "B", decimals: 1 },
  { id: "s2", label: "Pro clubs & federations", value: 142, suffix: "+", decimals: 0 },
  { id: "s3", label: "Inference latency", value: 38, suffix: "ms", decimals: 0 },
  { id: "s4", label: "Platform uptime", value: 99.98, suffix: "%", decimals: 2 },
];
