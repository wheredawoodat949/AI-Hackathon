import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { insights as seedInsights, matchInsights as seedMatchups } from "@/data";
import type { Insight, MatchInsight } from "@/data/types";
import { sportById, type SportId } from "@/data/sports";

export interface UploadedFileMeta {
  name: string;
  size: number;
  type: string;
}

export interface UploadedGame {
  id: string;
  sport: SportId;
  team: string;
  opponent: string;
  date: string;
  homeAway: "home" | "away";
  venue: string;
  competition: string;
  scoreFor: string;
  scoreAgainst: string;
  notes: string;
  files: UploadedFileMeta[];
  createdAt: number;
}

interface AppDataValue {
  matchups: MatchInsight[];
  insights: Insight[];
  uploads: UploadedGame[];
  addUploadedGame: (game: UploadedGame) => void;
}

const AppDataContext = createContext<AppDataValue | null>(null);

const clamp = (n: number, lo: number, hi: number) =>
  Math.max(lo, Math.min(hi, n));

function formatDate(iso: string): string {
  if (!iso) return "TBD";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/** Turn an uploaded game into a matchup + insight entry for the dashboard. */
function deriveEntries(game: UploadedGame): {
  matchup: MatchInsight;
  insight: Insight;
} {
  const sport = sportById(game.sport);
  const isHome = game.homeAway === "home";
  const f = Number.parseInt(game.scoreFor, 10);
  const a = Number.parseInt(game.scoreAgainst, 10);
  const hasScore = !Number.isNaN(f) && !Number.isNaN(a);

  const diff = hasScore ? f - a : 0;
  const ourWin = clamp(46 + diff * 7, 14, 84);
  const drawShare = game.sport === "soccer" ? clamp(26 - Math.abs(diff) * 4, 8, 28) : 3;
  const oppWin = clamp(100 - ourWin - drawShare, 6, 82);

  const homeWin = Math.round(isHome ? ourWin : oppWin);
  const awayWin = Math.round(isHome ? oppWin : ourWin);
  const draw = Math.max(0, 100 - homeWin - awayWin);

  const fixture = isHome
    ? `${game.team} vs ${game.opponent}`
    : `${game.opponent} vs ${game.team}`;

  const projectedScore = hasScore
    ? isHome
      ? `${f} – ${a}`
      : `${a} – ${f}`
    : "Pending";

  const matchup: MatchInsight = {
    id: `up-m-${game.id}`,
    fixture,
    competition: `${game.competition} · uploaded`,
    kickoff: formatDate(game.date),
    homeWin,
    draw,
    awayWin,
    projectedScore,
    edge: game.notes.trim()
      ? game.notes.trim().slice(0, 96)
      : `${sport.name} film queued — model breakdown in progress`,
  };

  const insight: Insight = {
    id: `up-i-${game.id}`,
    kind: "scouting",
    title: `Film added: ${game.team} vs ${game.opponent}`,
    detail: game.notes.trim()
      ? game.notes.trim()
      : `${game.files.length} ${sport.name.toLowerCase()} clip${
          game.files.length === 1 ? "" : "s"
        } uploaded and queued for automated breakdown.`,
    time: "just now",
    metric: hasScore ? `${f}–${a}` : sport.name,
  };

  return { matchup, insight };
}

export function AppDataProvider({ children }: { children: ReactNode }) {
  const [matchups, setMatchups] = useState<MatchInsight[]>(seedMatchups);
  const [insights, setInsights] = useState<Insight[]>(seedInsights);
  const [uploads, setUploads] = useState<UploadedGame[]>([]);

  const addUploadedGame = useCallback((game: UploadedGame) => {
    const { matchup, insight } = deriveEntries(game);
    setUploads((prev) => [game, ...prev]);
    setMatchups((prev) => [matchup, ...prev]);
    setInsights((prev) => [insight, ...prev]);
  }, []);

  const value = useMemo<AppDataValue>(
    () => ({ matchups, insights, uploads, addUploadedGame }),
    [matchups, insights, uploads, addUploadedGame],
  );

  return (
    <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>
  );
}

export function useAppData(): AppDataValue {
  const ctx = useContext(AppDataContext);
  if (!ctx) {
    throw new Error("useAppData must be used within an AppDataProvider");
  }
  return ctx;
}
