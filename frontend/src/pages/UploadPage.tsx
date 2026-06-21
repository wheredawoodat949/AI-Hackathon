import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { ArrowLeft, ArrowRight, Sparkles } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { FileDropzone } from "@/components/upload/FileDropzone";
import { SportSelector } from "@/components/upload/SportSelector";
import { GameDetailsForm } from "@/components/upload/GameDetailsForm";
import { ReviewStep } from "@/components/upload/ReviewStep";
import { AnalysisLoading } from "@/components/upload/AnalysisLoading";
import { AnalysisResult } from "@/components/upload/AnalysisResult";
import { StepIndicator, type Step } from "@/components/upload/StepIndicator";
import {
  validateVideo,
  type GameDetails,
  type UploadItem,
} from "@/components/upload/types";
import { sportById, type SportId } from "@/data/sports";
import { useAppData, type UploadedGame } from "@/store/appData";

const STEPS: Step[] = [
  { id: "upload", label: "Upload" },
  { id: "sport", label: "Sport" },
  { id: "details", label: "Game details" },
  { id: "review", label: "Review" },
];

const makeDetails = (sport: SportId): GameDetails => {
  const cfg = sportById(sport);
  return {
    team: cfg.defaultTeam,
    opponent: "",
    date: "",
    homeAway: "home",
    venue: "",
    competition: cfg.competitions[0],
    season: "2025/26",
    scoreFor: "",
    scoreAgainst: "",
    notes: "",
  };
};

const uid = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

export function UploadPage() {
  const { addUploadedGame } = useAppData();

  const [step, setStep] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [items, setItems] = useState<UploadItem[]>([]);
  const [sport, setSport] = useState<SportId>("soccer");
  const [details, setDetails] = useState<GameDetails>(() =>
    makeDetails("soccer"),
  );
  const [dropError, setDropError] = useState<string | null>(null);

  // Keep a ref so the unmount cleanup can revoke object URLs.
  const itemsRef = useRef(items);
  itemsRef.current = items;
  useEffect(
    () => () => {
      itemsRef.current.forEach(
        (i) => i.previewUrl && URL.revokeObjectURL(i.previewUrl),
      );
    },
    [],
  );

  // Simulate client-side upload progress.
  useEffect(() => {
    if (!items.some((i) => i.status === "uploading")) return;
    const timer = setInterval(() => {
      setItems((prev) =>
        prev.map((it) => {
          if (it.status !== "uploading") return it;
          const next = Math.min(100, it.progress + 6 + Math.random() * 16);
          return next >= 100
            ? { ...it, progress: 100, status: "ready" as const }
            : { ...it, progress: next };
        }),
      );
    }, 240);
    return () => clearInterval(timer);
  }, [items]);

  const addFiles = (files: File[]) => {
    setDropError(null);
    const valid: UploadItem[] = [];
    for (const file of files) {
      const err = validateVideo(file);
      if (err) {
        setDropError(err);
        continue;
      }
      valid.push({
        id: uid(),
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        previewUrl: file.type.startsWith("video/")
          ? URL.createObjectURL(file)
          : undefined,
        progress: 0,
        status: "uploading",
      });
    }
    if (valid.length) setItems((prev) => [...prev, ...valid]);
  };

  const removeItem = (id: string) => {
    setItems((prev) => {
      const target = prev.find((i) => i.id === id);
      if (target?.previewUrl) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((i) => i.id !== id);
    });
  };

  const changeSport = (next: SportId) => {
    const prevCfg = sportById(sport);
    const nextCfg = sportById(next);
    setSport(next);
    setDetails((d) => ({
      ...d,
      team: !d.team || d.team === prevCfg.defaultTeam ? nextCfg.defaultTeam : d.team,
      competition: nextCfg.competitions.includes(d.competition)
        ? d.competition
        : nextCfg.competitions[0],
    }));
  };

  const patchDetails = (patch: Partial<GameDetails>) =>
    setDetails((d) => ({ ...d, ...patch }));

  const readyCount = items.filter((i) => i.status === "ready").length;

  const stepValidity = useMemo(() => {
    return [
      readyCount > 0,
      true,
      details.team.trim().length > 0 && details.opponent.trim().length > 0,
      true,
    ];
  }, [readyCount, details.team, details.opponent]);

  const blockedHint = useMemo(() => {
    if (step === 0 && readyCount === 0)
      return items.length > 0 ? "Waiting for upload to finish" : "Add film to continue";
    if (step === 2 && !stepValidity[2])
      return "Enter your team and the opponent";
    return null;
  }, [step, readyCount, items.length, stepValidity]);

  const handleConfirm = () => {
    const cfg = sportById(sport);
    const game: UploadedGame = {
      id: uid(),
      sport,
      team: details.team.trim() || cfg.defaultTeam,
      opponent: details.opponent.trim() || "Opponent",
      date: details.date,
      homeAway: details.homeAway,
      venue: details.venue.trim(),
      competition: details.season.trim()
        ? `${details.competition} ${details.season.trim()}`
        : details.competition,
      scoreFor: details.scoreFor,
      scoreAgainst: details.scoreAgainst,
      notes: details.notes,
      files: items.map((i) => ({ name: i.name, size: i.size, type: i.type })),
      createdAt: Date.now(),
    };
    addUploadedGame(game);
    setSubmitted(true);
    setAnalyzing(true);
  };

  // Most recently added clip with a usable object URL — featured in the
  // post-analysis watch view.
  const featuredItem = useMemo(
    () => [...items].reverse().find((i) => i.previewUrl),
    [items],
  );

  const reset = () => {
    itemsRef.current.forEach(
      (i) => i.previewUrl && URL.revokeObjectURL(i.previewUrl),
    );
    setItems([]);
    setSport("soccer");
    setDetails(makeDetails("soccer"));
    setStep(0);
    setDropError(null);
    setSubmitted(false);
    setAnalyzing(false);
  };

  return (
    <DashboardLayout>
      <MotionConfig reducedMotion="user">
        <div className="mx-auto max-w-3xl">
          {/* Header */}
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold tracking-tight text-ink">
                Upload Film
              </h1>
              <Badge variant="accent">
                <Sparkles className="h-3 w-3" />
                Beta
              </Badge>
            </div>
            <p className="text-sm text-muted">
              Add game film and context — MotionCast queues it for automated breakdown
              and surfaces it across your workspace.
            </p>
          </div>

          {!submitted && (
            <div className="mt-6">
              <StepIndicator steps={STEPS} current={step} />
            </div>
          )}

          <Card className="mt-5 p-5 sm:p-6">
            {submitted ? (
              analyzing ? (
                <AnalysisLoading
                  sport={sport}
                  fileName={featuredItem?.name}
                  onComplete={() => setAnalyzing(false)}
                />
              ) : (
                <AnalysisResult
                  sport={sport}
                  details={details}
                  fileCount={items.length}
                  previewUrl={featuredItem?.previewUrl}
                  fileName={featuredItem?.name}
                  onReset={reset}
                />
              )
            ) : (
              <>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={step}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -12 }}
                    transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  >
                    {step === 0 && (
                      <section aria-labelledby="step-upload">
                        <h2
                          id="step-upload"
                          className="mb-1 text-sm font-medium text-ink"
                        >
                          Upload game film
                        </h2>
                        <p className="mb-4 text-xs text-muted">
                          Drop one or more clips. We'll generate previews and
                          queue them for analysis.
                        </p>
                        <FileDropzone
                          items={items}
                          onAddFiles={addFiles}
                          onRemove={removeItem}
                          error={dropError}
                        />
                      </section>
                    )}

                    {step === 1 && (
                      <section aria-labelledby="step-sport">
                        <h2
                          id="step-sport"
                          className="mb-1 text-sm font-medium text-ink"
                        >
                          Select the sport
                        </h2>
                        <p className="mb-4 text-xs text-muted">
                          This sets the analysis context and the models applied
                          to your film.
                        </p>
                        <SportSelector value={sport} onChange={changeSport} />
                      </section>
                    )}

                    {step === 2 && (
                      <section aria-labelledby="step-details">
                        <h2
                          id="step-details"
                          className="mb-1 text-sm font-medium text-ink"
                        >
                          Game details
                        </h2>
                        <p className="mb-4 text-xs text-muted">
                          Tell us about the match so insights are tagged
                          correctly.
                        </p>
                        <GameDetailsForm
                          sport={sport}
                          value={details}
                          onChange={patchDetails}
                        />
                      </section>
                    )}

                    {step === 3 && (
                      <section aria-labelledby="step-review">
                        <h2
                          id="step-review"
                          className="mb-1 text-sm font-medium text-ink"
                        >
                          Review & confirm
                        </h2>
                        <p className="mb-4 text-xs text-muted">
                          Check everything looks right before adding it to your
                          workspace.
                        </p>
                        <ReviewStep
                          items={items}
                          sport={sport}
                          details={details}
                        />
                      </section>
                    )}
                  </motion.div>
                </AnimatePresence>

                {/* Footer nav */}
                <div className="mt-6 flex items-center justify-between gap-3 border-t border-line pt-5">
                  {step === 0 ? (
                    <Link to="/app">
                      <Button variant="ghost" size="md">
                        Cancel
                      </Button>
                    </Link>
                  ) : (
                    <Button
                      variant="secondary"
                      size="md"
                      onClick={() => setStep((s) => Math.max(0, s - 1))}
                    >
                      <ArrowLeft className="h-4 w-4" />
                      Back
                    </Button>
                  )}

                  <div className="flex items-center gap-3">
                    {blockedHint && (
                      <span className="hidden text-xs text-faint sm:block">
                        {blockedHint}
                      </span>
                    )}
                    {step < STEPS.length - 1 ? (
                      <Button
                        size="md"
                        disabled={!stepValidity[step]}
                        onClick={() =>
                          setStep((s) => Math.min(STEPS.length - 1, s + 1))
                        }
                      >
                        Continue
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button size="md" onClick={handleConfirm}>
                        Confirm & add game
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </>
            )}
          </Card>
        </div>
      </MotionConfig>
    </DashboardLayout>
  );
}
