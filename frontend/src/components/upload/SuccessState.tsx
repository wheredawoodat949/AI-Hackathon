import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, CircleCheckBig, Plus } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { sportById, type SportId } from "@/data/sports";
import type { GameDetails } from "./types";

interface SuccessStateProps {
  sport: SportId;
  details: GameDetails;
  fileCount: number;
  onReset: () => void;
}

export function SuccessState({
  sport,
  details,
  fileCount,
  onReset,
}: SuccessStateProps) {
  const cfg = sportById(sport);
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="relative overflow-hidden rounded-2xl border border-line bg-surface/60 px-6 py-14 text-center"
    >
      <div className="bg-dot-grid pointer-events-none absolute inset-0 opacity-40" />
      <div className="pointer-events-none absolute inset-x-0 -top-20 mx-auto h-56 w-[70%] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(194,242,74,0.16),transparent_70%)] blur-2xl" />

      <div className="relative flex flex-col items-center">
        <motion.span
          initial={{ scale: 0.4, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 18, delay: 0.1 }}
          className="grid h-16 w-16 place-items-center rounded-2xl border border-accent/30 bg-accent/10 text-accent"
        >
          <CircleCheckBig className="h-8 w-8" />
        </motion.span>

        <h2 className="mt-5 text-2xl font-semibold tracking-tight text-ink">
          Film uploaded
        </h2>
        <p className="mt-2 max-w-md text-sm text-muted">
          {fileCount} {cfg.name.toLowerCase()} clip{fileCount === 1 ? "" : "s"} for{" "}
          <span className="text-ink">
            {details.team || cfg.defaultTeam} vs {details.opponent || "opponent"}
          </span>{" "}
          {fileCount === 1 ? "is" : "are"} queued for breakdown. We added it to your
          matchups and insight feed.
        </p>

        <div className="mt-7 flex flex-col items-center gap-3 sm:flex-row">
          <Link to="/app">
            <Button size="lg">
              View in dashboard
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Button size="lg" variant="secondary" onClick={onReset}>
            <Plus className="h-4 w-4" />
            Upload another
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
