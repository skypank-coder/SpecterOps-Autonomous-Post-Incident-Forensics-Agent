const LINKS = [
  { label: "How it works", href: "#how" },
  { label: "Live demo", href: "#demo" },
  { label: "Platform", href: "#features" },
  { label: "Impact", href: "#impact" },
];

export default function Footer() {
  return (
    <footer className="border-t border-white/8 bg-ink-950">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="flex flex-col items-center justify-between gap-8 md:flex-row md:items-start">
          <div className="max-w-sm text-center md:text-left">
            <div className="flex items-center justify-center gap-2.5 md:justify-start">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand to-brand-soft text-lg">
                👻
              </span>
              <span className="font-display text-lg font-bold text-white">
                Specter<span className="text-brand-soft">Ops</span>
              </span>
            </div>
            <p className="mt-4 text-sm text-zinc-500">
              Autonomous post-incident forensics. When your production dies at 3am, SpecterOps
              wakes up instead of you.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-x-7 gap-y-3">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="text-sm text-zinc-400 transition-colors hover:text-white"
              >
                {l.label}
              </a>
            ))}
          </div>
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-3 border-t border-white/8 pt-6 text-xs text-zinc-600 md:flex-row">
          <span>
            Built for the Google Cloud Rapid Agent Hackathon 2026 · Dynatrace Partner Track
          </span>
          <span>MIT Licensed · © 2026 SpecterOps Contributors</span>
        </div>
      </div>
    </footer>
  );
}
