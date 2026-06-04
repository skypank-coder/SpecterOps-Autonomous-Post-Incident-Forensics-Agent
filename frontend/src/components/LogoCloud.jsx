const TECH = [
  "Dynatrace",
  "Gemini 2.5 Flash",
  "Google Cloud Run",
  "FastAPI",
  "React + D3",
  "Server-Sent Events",
  "Firebase Hosting",
  "Python 3.11",
];

export default function LogoCloud() {
  const row = [...TECH, ...TECH];
  return (
    <section className="relative border-y border-white/5 bg-ink-950/60 py-10">
      <p className="mb-7 text-center text-xs uppercase tracking-[0.25em] text-zinc-600">
        Built on a production-grade observability + AI stack
      </p>
      <div className="relative overflow-hidden [mask-image:linear-gradient(to_right,transparent,#000_12%,#000_88%,transparent)]">
        <div className="flex w-max animate-marquee gap-12 pr-12">
          {row.map((t, i) => (
            <span
              key={i}
              className="whitespace-nowrap font-display text-lg font-semibold text-zinc-500/80 transition-colors hover:text-zinc-300"
            >
              {t}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
