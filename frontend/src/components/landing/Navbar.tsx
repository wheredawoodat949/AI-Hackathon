import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const links = [
  { label: "Platform", href: "#platform" },
  { label: "Features", href: "#features" },
  { label: "Metrics", href: "#metrics" },
  { label: "Customers", href: "#customers" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className="fixed inset-x-0 top-0 z-50 flex justify-center px-4 pt-3">
      <div
        className={cn(
          "flex w-full max-w-6xl items-center justify-between rounded-2xl px-3 py-2.5 transition-all duration-300",
          scrolled
            ? "border border-line bg-base/70 shadow-card backdrop-blur-xl"
            : "border border-transparent",
        )}
      >
        <Link to="/" aria-label="MotionCast home">
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="rounded-lg px-3 py-1.5 text-sm text-muted transition-colors hover:bg-white/[0.04] hover:text-ink"
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            to="/app"
            className="hidden rounded-lg px-3 py-1.5 text-sm text-muted transition-colors hover:text-ink sm:block"
          >
            Sign in
          </Link>
          <Link to="/app">
            <Button size="sm">
              Launch app
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
