import { motion } from "motion/react";
import { CalendarDays, Download, Filter } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/dashboard/StatCard";
import { PerformancePanel } from "@/components/dashboard/PerformancePanel";
import { MatchupCard } from "@/components/dashboard/MatchupCard";
import { Leaderboard } from "@/components/dashboard/Leaderboard";
import { InsightsFeed } from "@/components/dashboard/InsightsFeed";
import { PlayerDetailPanel } from "@/components/dashboard/PlayerDetailPanel";
import { kpis } from "@/data";

export function DashboardPage() {
  return (
    <DashboardLayout>
      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
      >
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight text-ink">
              Club Overview
            </h1>
            <Badge variant="accent">Season 25/26</Badge>
          </div>
          <p className="mt-1 text-sm text-muted">
            Model snapshot for Halston City · updated 12 seconds ago
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm">
            <CalendarDays className="h-3.5 w-3.5" />
            Last 12 weeks
          </Button>
          <Button variant="secondary" size="sm">
            <Filter className="h-3.5 w-3.5" />
            Filters
          </Button>
          <Button size="sm">
            <Download className="h-3.5 w-3.5" />
            Export
          </Button>
        </div>
      </motion.div>

      {/* KPI row */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((k, i) => (
          <StatCard key={k.id} kpi={k} index={i} />
        ))}
      </div>

      {/* Main grid */}
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <PerformancePanel />
        </div>
        <div className="lg:col-span-1">
          <MatchupCard />
        </div>

        <div className="lg:col-span-2">
          <Leaderboard />
        </div>
        <div className="lg:col-span-1">
          <InsightsFeed />
        </div>

        <div className="lg:col-span-3">
          <PlayerDetailPanel />
        </div>
      </div>
    </DashboardLayout>
  );
}
