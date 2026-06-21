import { Goal, Shield, Volleyball, type LucideIcon } from "lucide-react";

export type SportId = "soccer" | "basketball" | "football";

export interface SportConfig {
  id: SportId;
  name: string;
  icon: LucideIcon;
  /** Short descriptor shown under the sport name. */
  blurb: string;
  /** Label for the "our team" field. */
  teamLabel: string;
  /** Label used for the score readout (Goals vs Points). */
  scoreNoun: string;
  /** Default competition suggestions for the datalist. */
  competitions: string[];
  /** Default club to pre-fill (keeps soccer consistent with the app). */
  defaultTeam: string;
}

export const sports: SportConfig[] = [
  {
    id: "soccer",
    name: "Soccer",
    icon: Goal,
    blurb: "Event, tracking & xG models",
    teamLabel: "Your club",
    scoreNoun: "Goals",
    competitions: ["Apex Premier", "Apex Cup", "Continental League", "Friendly"],
    defaultTeam: "Halston City",
  },
  {
    id: "basketball",
    name: "Basketball",
    icon: Volleyball,
    blurb: "Possession & shot-quality models",
    teamLabel: "Your team",
    scoreNoun: "Points",
    competitions: ["Apex Hoops League", "National Cup", "Conference", "Exhibition"],
    defaultTeam: "Halston Hawks",
  },
  {
    id: "football",
    name: "Football",
    icon: Shield,
    blurb: "Drive, EPA & coverage models",
    teamLabel: "Your team",
    scoreNoun: "Points",
    competitions: ["Apex Gridiron League", "Division Title", "Conference", "Preseason"],
    defaultTeam: "Halston Sentinels",
  },
];

export const sportById = (id: SportId): SportConfig =>
  sports.find((s) => s.id === id) ?? sports[0];
