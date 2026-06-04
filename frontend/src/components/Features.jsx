import {
  Network,
  Radio,
  GitBranch,
  FileText,
  ShieldCheck,
  Boxes,
} from "lucide-react";
import Reveal from "./Reveal.jsx";

const FEATURES = [
  {
    icon: Network,
    title: "Deep Dynatrace integration",
    body: "One async client wraps five v2 endpoints — problems, traces, logs, metrics and topology — pulled in parallel for speed.",
    accent: "text-brand-soft",
  },
  {
    icon: Radio,
    title: "Real-time SSE streaming",
    body: "Every agent broadcasts start and completion events. The console updates live as the investigation unfolds.",
    accent: "text-cyan",
  },
  {
    icon: GitBranch,
    title: "Causal graph reasoning",
    body: "Not just a timeline — a directed graph of cause and effect, with the single root cause isolated and scored.",
    accent: "text-mint",
  },
  {
    icon: FileText,
    title: "Gemini-authored post-mortems",
    body: "A complete, 10-section incident report with impact, remediation steps and action items — ready to ship.",
    accent: "text-amber",
  },
  {
    icon: ShieldCheck,
    title: "Resilient by design",
    body: "A model-fallback chain and scenario-accurate offline mode mean the demo never breaks — even with zero accounts.",
    accent: "text-brand-soft",
  },
  {
    icon: Boxes,
    title: "Production-ready stack",
    body: "FastAPI + Cloud Run, a tested pipeline, CI on every push, and an MIT license. Built to actually run.",
    accent: "text-cyan",
  },
];

export default function Features() {
  return (
    <section id="features" className="section">
      <Reveal className="mx-auto max-w-2xl text-center">
        <span className="eyebrow mb-5">The platform</span>
        <h2 className="font-display text-4xl font-bold tracking-tight text-white md:text-5xl">
          Everything an autonomous SRE needs.
        </h2>
        <p className="mt-5 text-zinc-400">
          From signal collection to a finished report — SpecterOps owns the entire forensic loop.
        </p>
      </Reveal>

      <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f, i) => (
          <Reveal key={f.title} delay={(i % 3) * 0.08}>
            <div className="card group h-full transition-all duration-300 hover:-translate-y-1 hover:border-white/20">
              <div className={`mb-4 grid h-11 w-11 place-items-center rounded-xl border border-white/10 bg-white/[0.04] ${f.accent}`}>
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="font-display text-base font-semibold text-white">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-400">{f.body}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
