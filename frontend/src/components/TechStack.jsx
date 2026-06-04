import Reveal from "./Reveal.jsx";

const STACK = [
  { layer: "Agents & Backend", value: "Python · FastAPI · asyncio · SSE" },
  { layer: "Reasoning", value: "Google Gemini 2.5 Flash (google-genai)" },
  { layer: "Observability", value: "Dynatrace v2 API — traces · logs · metrics" },
  { layer: "Frontend", value: "React · Vite · Tailwind · D3 · Three.js" },
  { layer: "Deployment", value: "Docker → Cloud Run · Firebase Hosting" },
  { layer: "Quality", value: "pytest · GitHub Actions CI · MIT license" },
];

export default function TechStack() {
  return (
    <section className="section">
      <div className="grid items-center gap-12 lg:grid-cols-[0.8fr_1.2fr]">
        <Reveal>
          <span className="eyebrow mb-5">Under the hood</span>
          <h2 className="font-display text-4xl font-bold tracking-tight text-white md:text-5xl">
            Engineered like a product, not a prototype.
          </h2>
          <p className="mt-6 text-zinc-400">
            SpecterOps is a real, deployable system: parallel data gathering, graceful fallbacks,
            a tested pipeline and continuous integration. Open the repo and run it in five commands.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <a href="#demo" className="btn-primary">Try the live demo</a>
            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="btn-ghost"
            >
              View source
            </a>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-ink-900/60 backdrop-blur-md">
            {STACK.map((s, i) => (
              <div
                key={s.layer}
                className={`flex flex-col gap-1 px-6 py-5 sm:flex-row sm:items-center sm:justify-between ${
                  i !== STACK.length - 1 ? "border-b border-white/8" : ""
                }`}
              >
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  {s.layer}
                </span>
                <span className="font-mono text-sm text-zinc-200">{s.value}</span>
              </div>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
