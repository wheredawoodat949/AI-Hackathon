import { Link } from "react-router-dom";
import { Logo } from "@/components/ui/Logo";

const columns = [
  {
    title: "Product",
    links: ["Win Probability", "Player Models", "Opponent Scouting", "Film Room", "Changelog"],
  },
  {
    title: "Company",
    links: ["About", "Customers", "Careers", "Press", "Security"],
  },
  {
    title: "Resources",
    links: ["Documentation", "API Reference", "Methodology", "Status", "Contact"],
  },
];

export function Footer() {
  return (
    <footer className="relative border-t border-line">
      <div className="mx-auto max-w-6xl px-4 py-14">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(3,1fr)]">
          <div>
            <Logo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted">
              The performance intelligence platform for elite football
              organizations.
            </p>
            <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-line bg-surface/60 px-3 py-1 text-xs text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-pos" />
              All systems operational
            </div>
          </div>

          {columns.map((col) => (
            <div key={col.title}>
              <p className="text-xs font-medium uppercase tracking-wider text-faint">
                {col.title}
              </p>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((l) => (
                  <li key={l}>
                    <a
                      href="#"
                      className="text-sm text-muted transition-colors hover:text-ink"
                    >
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-line pt-6 text-xs text-faint sm:flex-row">
          <p>© {new Date().getFullYear()} MotionCast, Inc. All rights reserved.</p>
          <div className="flex items-center gap-5">
            <a href="#" className="transition-colors hover:text-muted">
              Privacy
            </a>
            <a href="#" className="transition-colors hover:text-muted">
              Terms
            </a>
            <Link to="/app" className="transition-colors hover:text-muted">
              Launch app
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
