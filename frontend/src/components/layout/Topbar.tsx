import { Link } from "react-router-dom";
import { Bell, ChevronDown, Command, Menu, Search, Upload } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

export function Topbar({
  onMenu,
  className,
}: {
  onMenu?: () => void;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-line bg-base/70 px-4 backdrop-blur-xl md:px-6",
        className,
      )}
    >
      <button
        type="button"
        onClick={onMenu}
        className="grid h-9 w-9 place-items-center rounded-lg border border-line text-muted hover:text-ink lg:hidden"
        aria-label="Open navigation"
      >
        <Menu className="h-4 w-4" />
      </button>

      <div className="hidden items-center gap-2 md:flex">
        <span className="text-sm font-medium text-ink">Halston City</span>
        <ChevronDown className="h-3.5 w-3.5 text-faint" />
        <Badge variant="accent" className="ml-1">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" />
          1st · Apex Premier
        </Badge>
      </div>

      <div className="ml-auto flex items-center gap-2">
        <label className="group hidden items-center gap-2 rounded-lg border border-line bg-surface/60 px-3 py-2 text-sm text-muted transition-colors focus-within:border-line-strong sm:flex">
          <Search className="h-4 w-4 text-faint" />
          <input
            type="text"
            placeholder="Search players, fixtures…"
            className="w-44 bg-transparent text-ink placeholder:text-faint focus:outline-none lg:w-56"
            aria-label="Search"
          />
          <kbd className="hidden items-center gap-0.5 rounded border border-line px-1.5 py-0.5 font-mono text-[10px] text-faint lg:flex">
            <Command className="h-2.5 w-2.5" />K
          </kbd>
        </label>

        <Link to="/app/upload" className="hidden sm:block">
          <Button size="sm">
            <Upload className="h-3.5 w-3.5" />
            <span className="hidden md:inline">Upload Film</span>
          </Button>
        </Link>

        <button
          type="button"
          className="relative grid h-9 w-9 place-items-center rounded-lg border border-line text-muted transition-colors hover:text-ink"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-accent" />
        </button>

        <Link
          to="/"
          className="flex items-center gap-2 rounded-lg border border-line bg-surface/60 py-1 pl-1 pr-2.5 transition-colors hover:border-line-strong"
        >
          <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-emerald to-accent text-xs font-semibold text-base">
            DM
          </span>
          <span className="hidden text-xs leading-tight sm:block">
            <span className="block font-medium text-ink">D. Moreno</span>
            <span className="block text-faint">Head Analyst</span>
          </span>
        </Link>
      </div>
    </header>
  );
}
