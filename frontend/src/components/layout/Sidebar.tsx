import { NavLink } from "react-router-dom";
import {
  Activity,
  CalendarClock,
  ChartLine,
  CircleDot,
  CloudUpload,
  Compass,
  LayoutDashboard,
  LifeBuoy,
  Settings,
  Shield,
  Users,
  Video,
} from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  icon: typeof Activity;
  to: string;
  badge?: string;
  end?: boolean;
}

const primaryNav: NavItem[] = [
  { label: "Overview", icon: LayoutDashboard, to: "/app", end: true },
  { label: "Performance", icon: ChartLine, to: "/app/performance" },
  { label: "Players", icon: Users, to: "/app/players" },
  { label: "Matchups", icon: Compass, to: "/app/matchups", badge: "3" },
  { label: "Opposition", icon: Shield, to: "/app/opposition" },
  { label: "Film Room", icon: Video, to: "/app/film" },
  { label: "Upload Film", icon: CloudUpload, to: "/app/upload" },
];

const secondaryNav: NavItem[] = [
  { label: "Fixtures", icon: CalendarClock, to: "/app/fixtures" },
  { label: "Fitness", icon: Activity, to: "/app/fitness" },
  { label: "Settings", icon: Settings, to: "/app/settings" },
];

function NavSection({ items, label }: { items: NavItem[]; label?: string }) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <p className="px-3 pb-1 pt-3 text-[10px] font-medium uppercase tracking-[0.14em] text-faint">
          {label}
        </p>
      )}
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) =>
            cn(
              "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              isActive
                ? "bg-white/[0.05] text-ink"
                : "text-muted hover:bg-white/[0.03] hover:text-ink",
            )
          }
        >
          {({ isActive }) => (
            <>
              <span
                className={cn(
                  "absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-accent transition-opacity",
                  isActive ? "opacity-100" : "opacity-0",
                )}
              />
              <item.icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-colors",
                  isActive
                    ? "text-accent"
                    : "text-faint group-hover:text-muted",
                )}
              />
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <span className="rounded-full border border-accent/25 bg-accent/10 px-1.5 text-[10px] font-medium text-accent">
                  {item.badge}
                </span>
              )}
            </>
          )}
        </NavLink>
      ))}
    </div>
  );
}

export function Sidebar({ className }: { className?: string }) {
  return (
    <aside
      className={cn(
        "flex h-full w-64 shrink-0 flex-col border-r border-line bg-panel/60",
        className,
      )}
    >
      <div className="flex h-16 items-center border-b border-line px-5">
        <Logo />
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <NavSection items={primaryNav} />
        <div className="my-3 border-t border-line" />
        <NavSection items={secondaryNav} label="Workspace" />
      </nav>

      <div className="border-t border-line p-3">
        <div className="flex items-center gap-3 rounded-xl border border-line bg-surface/60 p-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <CircleDot className="h-4 w-4" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-ink">
              Live data feed
            </p>
            <p className="truncate text-[11px] text-faint">
              Synced 12s ago
            </p>
          </div>
        </div>
        <a
          href="#"
          className="mt-2 flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted transition-colors hover:bg-white/[0.03] hover:text-ink"
        >
          <LifeBuoy className="h-4 w-4 text-faint" />
          Help & docs
        </a>
      </div>
    </aside>
  );
}
