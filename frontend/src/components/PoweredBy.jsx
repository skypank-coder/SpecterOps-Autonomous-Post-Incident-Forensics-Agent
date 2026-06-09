import { Brain, Plug, Cloud, Flame, Database, Activity } from "lucide-react";
import Reveal from "./Reveal.jsx";

const STACK = [
  {
    icon: Brain,
    name: "Google Gemini 2.5 Flash",
    tag: "Vertex AI · Google Cloud",
    body: "The reasoning core. Classifies the alert, reconstructs the timeline, builds the causal graph and authors the post-mortem.",
    accent: "text-brand-soft",
    ring: "shadow-glow",
  },
  {
    icon: Plug,
    name: "Dynatrace MCP Server",
    tag: "@dynatrace-oss/dynatrace-mcp-server",
    body: "The partner integration — over the Model Context Protocol. The agent calls real MCP tools: list_problems · execute_dql · find_entity_by_name.",
    accent: "text-[#9b82ff]",
    ring: "shadow-[0_0_40px_-10px_rgba(118,55,255,0.55)]",
  },
  {
    icon: Cloud,
    name: "Google Cloud Run",
    tag: "Serverless backend",
    body: "Hosts the autonomous four-agent backend (FastAPI + Server-Sent Events) on Google Cloud, container-deployed.",
    accent: "text-cyan",
    ring: "shadow-[0_0_40px_-10px_rgba(34,211,238,0.5)]",
  },
  {
    icon: Flame,
    name: "Firebase",
    tag: "Auth + Hosting · Google Cloud",
    body: "Real Google / email sign-in and the global CDN that serves the dashboard.",
    accent: "text-amber",
    ring: "shadow-[0_0_40px_-10px_rgba(245,166,35,0.5)]",
  },
  {
    icon: Database,
    name: "Cloud Firestore",
    tag: "Persistence · Google Cloud",
    body: "Every investigation is saved to a Google Cloud database and survives restarts.",
    accent: "text-mint",
    ring: "shadow-glow-mint",
  },
  {
    icon: Activity,
    name: "React · D3 · Three.js",
    tag: "Real-time dashboard",
    body: "Live SSE updates, a force-directed causal graph, a 3D hero — a business-grade UI.",
    accent: "text-rose",
    ring: "shadow-[0_0_40px_-10px_rgba(255,77,109,0.5)]",
  },
];

export default function PoweredBy() {
  return (
    <section id="stack" className="section spotlight">
      <Reveal className="mx-auto max-w-2xl text-center">
        <span className="eyebrow mb-5">Powered by</span>
        <h2 className="font-display text-4xl font-bold tracking-tight text-white md:text-5xl">
          The stack that makes it <span className="gradient-text">real</span>.
        </h2>
        <p className="mt-5 text-zinc-400">
          Built end-to-end on <strong className="text-white">Google Cloud</strong> and the official{" "}
          <strong className="text-white">Dynatrace MCP server</strong> for the Google Cloud Rapid
          Agent Hackathon — Dynatrace Partner Track.
        </p>
      </Reveal>

      <div className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {STACK.map((s, i) => (
          <Reveal key={s.name} delay={(i % 3) * 0.08}>
            <div className="card group h-full transition-all duration-300 hover:-translate-y-1 hover:border-white/20">
              <div
                className={`mb-4 grid h-12 w-12 place-items-center rounded-xl border border-white/10 bg-ink-850 ${s.accent} ${s.ring} transition-transform duration-300 group-hover:scale-110`}
              >
                <s.icon className="h-6 w-6" />
              </div>
              <h3 className="font-display text-base font-semibold text-white">{s.name}</h3>
              <div className={`mt-0.5 font-mono text-[11px] ${s.accent}`}>{s.tag}</div>
              <p className="mt-3 text-sm leading-relaxed text-zinc-400">{s.body}</p>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal delay={0.2} className="mt-10">
        <div className="flex flex-wrap items-center justify-center gap-2 text-[11px]">
          {[
            "Google Cloud Run",
            "Vertex AI",
            "Gemini 2.5 Flash",
            "Dynatrace MCP",
            "Firebase Auth",
            "Cloud Firestore",
            "FastAPI · SSE",
            "MIT Licensed",
          ].map((t) => (
            <span
              key={t}
              className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 font-medium text-zinc-300"
            >
              {t}
            </span>
          ))}
        </div>
      </Reveal>
    </section>
  );
}
