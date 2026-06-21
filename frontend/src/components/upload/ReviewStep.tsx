import { Film } from "lucide-react";
import { sportById, type SportId } from "@/data/sports";
import { formatBytes } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { GameDetails, UploadItem } from "./types";

interface ReviewStepProps {
  items: UploadItem[];
  sport: SportId;
  details: GameDetails;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <span className="text-xs text-muted">{label}</span>
      <span className="max-w-[60%] text-right text-sm font-medium text-ink">
        {value || "—"}
      </span>
    </div>
  );
}

export function ReviewStep({ items, sport, details }: ReviewStepProps) {
  const cfg = sportById(sport);
  const hasScore = details.scoreFor !== "" && details.scoreAgainst !== "";
  const score = hasScore
    ? `${details.scoreFor} – ${details.scoreAgainst}`
    : "Not recorded";

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {/* Film summary */}
      <div className="rounded-xl border border-line bg-surface/60 p-4">
        <p className="text-xs font-medium uppercase tracking-wider text-faint">
          Film ({items.length})
        </p>
        <div className="mt-3 flex flex-col gap-2">
          {items.map((item) => (
            <div key={item.id} className="flex items-center gap-3">
              <div className="grid h-9 w-12 shrink-0 place-items-center overflow-hidden rounded-md border border-line bg-base">
                {item.previewUrl ? (
                  <video
                    src={item.previewUrl}
                    muted
                    playsInline
                    preload="metadata"
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <Film className="h-4 w-4 text-faint" />
                )}
              </div>
              <span className="min-w-0 flex-1 truncate text-sm text-ink">
                {item.name}
              </span>
              <span className="tnum shrink-0 text-xs text-faint">
                {formatBytes(item.size)}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center gap-2 border-t border-line pt-3">
          <span className="grid h-8 w-8 place-items-center rounded-lg border border-accent/30 bg-accent/10 text-accent">
            <cfg.icon className="h-4 w-4" />
          </span>
          <div>
            <p className="text-sm font-medium text-ink">{cfg.name}</p>
            <p className="text-[11px] text-faint">Analysis context</p>
          </div>
        </div>
      </div>

      {/* Game info summary */}
      <div className="rounded-xl border border-line bg-surface/60 p-4">
        <p className="text-xs font-medium uppercase tracking-wider text-faint">
          Game details
        </p>
        <div className="mt-1 divide-y divide-line/60">
          <Row
            label="Fixture"
            value={`${details.team || cfg.defaultTeam} vs ${details.opponent || "—"}`}
          />
          <Row
            label="Date"
            value={
              details.date
                ? new Date(details.date).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })
                : ""
            }
          />
          <Row
            label="Venue"
            value={`${details.homeAway === "home" ? "Home" : "Away"}${
              details.venue ? ` · ${details.venue}` : ""
            }`}
          />
          <Row
            label="Competition"
            value={`${details.competition}${
              details.season ? ` · ${details.season}` : ""
            }`}
          />
          <Row label={`Final score (${cfg.scoreNoun})`} value={score} />
        </div>

        {details.notes.trim() && (
          <div className={cn("mt-3 rounded-lg border border-line bg-base/60 p-3")}>
            <p className="text-[11px] uppercase tracking-wider text-faint">
              Notes
            </p>
            <p className="mt-1 text-xs leading-relaxed text-muted">
              {details.notes.trim()}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
