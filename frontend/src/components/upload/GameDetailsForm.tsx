import { useId } from "react";
import { Home, Plane } from "lucide-react";
import { Field, Input, Select, Segmented, Textarea } from "@/components/ui/form";
import { sportById, type SportId } from "@/data/sports";
import type { GameDetails } from "./types";

interface GameDetailsFormProps {
  sport: SportId;
  value: GameDetails;
  onChange: (patch: Partial<GameDetails>) => void;
}

export function GameDetailsForm({
  sport,
  value,
  onChange,
}: GameDetailsFormProps) {
  const cfg = sportById(sport);
  const ids = useId();
  const fid = (name: string) => `${ids}-${name}`;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <Field label={cfg.teamLabel} htmlFor={fid("team")}>
        <Input
          id={fid("team")}
          value={value.team}
          onChange={(e) => onChange({ team: e.target.value })}
          placeholder={cfg.defaultTeam}
        />
      </Field>

      <Field label="Opponent" htmlFor={fid("opp")}>
        <Input
          id={fid("opp")}
          value={value.opponent}
          onChange={(e) => onChange({ opponent: e.target.value })}
          placeholder="e.g. Ravenport United"
        />
      </Field>

      <Field label="Match date" htmlFor={fid("date")}>
        <Input
          id={fid("date")}
          type="date"
          value={value.date}
          onChange={(e) => onChange({ date: e.target.value })}
          className="[color-scheme:dark]"
        />
      </Field>

      <Field label="Venue" htmlFor={fid("venue")}>
        <div className="flex items-center gap-2">
          <Segmented
            ariaLabel="Home or away"
            value={value.homeAway}
            onChange={(v) => onChange({ homeAway: v })}
            options={[
              { value: "home", label: "Home", icon: Home },
              { value: "away", label: "Away", icon: Plane },
            ]}
          />
          <Input
            id={fid("venue")}
            value={value.venue}
            onChange={(e) => onChange({ venue: e.target.value })}
            placeholder="Stadium"
            className="flex-1"
            aria-label="Venue name"
          />
        </div>
      </Field>

      <Field label="Competition" htmlFor={fid("comp")}>
        <Select
          id={fid("comp")}
          value={value.competition}
          onChange={(e) => onChange({ competition: e.target.value })}
        >
          {cfg.competitions.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </Select>
      </Field>

      <Field label="Season" htmlFor={fid("season")}>
        <Input
          id={fid("season")}
          value={value.season}
          onChange={(e) => onChange({ season: e.target.value })}
          placeholder="2025/26"
        />
      </Field>

      <Field label={`${cfg.scoreNoun} — your team`} htmlFor={fid("sf")} optional>
        <Input
          id={fid("sf")}
          type="number"
          min={0}
          inputMode="numeric"
          value={value.scoreFor}
          onChange={(e) => onChange({ scoreFor: e.target.value })}
          placeholder="0"
        />
      </Field>

      <Field label={`${cfg.scoreNoun} — opponent`} htmlFor={fid("sa")} optional>
        <Input
          id={fid("sa")}
          type="number"
          min={0}
          inputMode="numeric"
          value={value.scoreAgainst}
          onChange={(e) => onChange({ scoreAgainst: e.target.value })}
          placeholder="0"
        />
      </Field>

      <Field
        label="Notes & analysis objectives"
        htmlFor={fid("notes")}
        className="sm:col-span-2"
        hint="What should the model focus on? Tactics, key players, phases of play."
        optional
      >
        <Textarea
          id={fid("notes")}
          value={value.notes}
          onChange={(e) => onChange({ notes: e.target.value })}
          placeholder="e.g. Break down our high press vs their 3-4-3 build-out and chances created from the left half-space."
        />
      </Field>
    </div>
  );
}
