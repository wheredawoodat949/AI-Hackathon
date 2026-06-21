const partners = [
  "Halston City",
  "Ravenport United",
  "Kingsbridge FC",
  "Meridian Athletic",
  "Ashford Rovers",
  "Norfield United",
  "Carrick Town",
  "Sefton Wanderers",
  "Brakemoor FC",
  "Vellmont City",
];

export function LogoCloud() {
  const row = [...partners, ...partners];
  return (
    <section id="customers" className="relative border-y border-line py-10">
      <p className="mb-7 text-center text-xs uppercase tracking-[0.18em] text-faint">
        Powering analysis for the world's most ambitious clubs
      </p>
      <div className="mask-fade-x overflow-hidden">
        <div className="flex w-max animate-marquee items-center gap-12 motion-reduce:animate-none">
          {row.map((name, i) => (
            <span
              key={i}
              className="flex shrink-0 items-center gap-2 whitespace-nowrap text-sm font-medium text-muted/70"
            >
              <span className="grid h-6 w-6 place-items-center rounded border border-line bg-surface font-mono text-[9px] text-faint">
                {name
                  .split(" ")
                  .map((w) => w[0])
                  .join("")
                  .slice(0, 3)}
              </span>
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
