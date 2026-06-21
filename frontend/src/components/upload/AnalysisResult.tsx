import { useRef } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import {
  ArrowRight,
  CircleCheckBig,
  Expand,
  Film,
  Plus,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { sportById, type SportId } from "@/data/sports";
import type { GameDetails } from "./types";

interface AnalysisResultProps {
  sport: SportId;
  details: GameDetails;
  fileCount: number;
  previewUrl?: string;
  fileName?: string;
  onReset: () => void;
}

const INSIGHTS = [
  { label: "Possession", value: "57%" },
  { label: "xG", value: "1.84" },
  { label: "Sprints", value: "63" },
  { label: "Top speed", value: "34.1 km/h" },
  { label: "Players tracked", value: "22" },
];

export function AnalysisResult({
  sport,
  details,
  fileCount,
  previewUrl,
  fileName,
  onReset,
}: AnalysisResultProps) {
  const cfg = sportById(sport);
  const frameRef = useRef<HTMLDivElement>(null);

  const goFullscreen = () => {
    const el = frameRef.current;
    if (!el) return;
    if (document.fullscreenElement) {
      void document.exitFullscreen();
    } else {
      void el.requestFullscreen?.();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col gap-6"
    >
      {/* result banner */}
      <div className="flex items-center gap-3">
        <motion.span
          initial={{ scale: 0.4, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 18 }}
          className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-accent/30 bg-accent/10 text-accent"
        >
          <CircleCheckBig className="h-5 w-5" />
        </motion.span>
        <div className="min-w-0">
          <h2 className="text-base font-semibold tracking-tight text-ink">
            Analysis complete
          </h2>
          <p className="truncate text-xs text-muted">
            {details.team || cfg.defaultTeam} vs{" "}
            {details.opponent || "opponent"} · {cfg.name}
          </p>
        </div>
        <span className="ml-auto inline-flex items-center gap-1 rounded-full border border-accent/25 bg-accent/10 px-2.5 py-1 text-[11px] font-medium text-accent">
          <Sparkles className="h-3 w-3" /> Ready to watch
        </span>
      </div>

      {/* big watch player */}
      <div className="relative rounded-2xl border border-line-strong bg-panel/80 p-1.5 shadow-glow">
        {/* window chrome */}
        <div className="flex items-center gap-2 px-3 py-2">
          <span className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
          </span>
          <div className="mx-auto flex items-center gap-2 truncate rounded-md border border-line bg-base/60 px-3 py-1 font-mono text-[10px] text-faint">
            <Film className="h-3 w-3 text-accent" />
            <span className="truncate">{fileName ?? "game-film.mp4"}</span>
          </div>
          <button
            type="button"
            onClick={goFullscreen}
            className="inline-flex items-center gap-1.5 rounded-md border border-line bg-base/60 px-2.5 py-1 text-[11px] font-medium text-muted transition-colors hover:border-accent/40 hover:text-accent"
            aria-label="Watch fullscreen"
          >
            <Expand className="h-3.5 w-3.5" />
            Fullscreen
          </button>
        </div>

        <div
          ref={frameRef}
          className="group relative aspect-video overflow-hidden rounded-xl border border-line bg-black"
        >
          {previewUrl ? (
            <video
              src={previewUrl}
              autoPlay
              muted
              loop
              playsInline
              controls
              className="h-full w-full bg-black object-contain"
            />
          ) : (
            <div className="grid h-full w-full place-items-center text-faint">
              <Film className="h-8 w-8" />
            </div>
          )}

          {/* corner HUD tag */}
          <div className="pointer-events-none absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-md border border-accent/30 bg-base/70 px-2 py-1 font-mono text-[10px] font-medium text-accent backdrop-blur-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-accent motion-safe:animate-ping" />
            CV TRACKING
          </div>
        </div>
      </div>

      {/* analysis insight chips */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {INSIGHTS.map((m, i) => (
          <motion.div
            key={m.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 + i * 0.06 }}
            className="rounded-xl border border-line bg-surface/60 px-3 py-2.5"
          >
            <p className="text-[11px] text-faint">{m.label}</p>
            <p className="tnum mt-0.5 font-mono text-lg font-semibold text-ink">
              {m.value}
            </p>
          </motion.div>
        ))}
      </div>

      {/* actions */}
      <div className="flex flex-col items-start justify-between gap-3 border-t border-line pt-5 sm:flex-row sm:items-center">
        <p className="text-xs text-muted">
          {fileCount} clip{fileCount === 1 ? "" : "s"} analyzed and added to your
          matchups & insight feed.
        </p>
        <div className="flex items-center gap-3">
          <Button variant="secondary" size="md" onClick={onReset}>
            <Plus className="h-4 w-4" />
            Upload another
          </Button>
          <Link to="/app">
            <Button size="md">
              View in dashboard
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </motion.div>
  );
}
