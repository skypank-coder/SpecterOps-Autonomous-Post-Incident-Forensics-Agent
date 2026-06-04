import { motion } from "framer-motion";
import Reveal from "./Reveal.jsx";

const AGENTS = [
  {
    n: "01",
    emoji: "🛡️",
    name: "SentinelAgent",
    role: "Triage & classify",
    body: "Parses the incoming Dynatrace alert, extracts the primary service, severity and failure category, and decides which signals to investigate.",
    accent: "text-brand-soft",
    ring: "shadow-glow",
  },
  {
    n: "02",
    emoji: "🔍",
    name: "TraceArchaeologist",
    role: "Investigate in parallel",
    body: "Pulls distributed traces, logs, metrics and service topology from the Dynatrace MCP simultaneously, then reconstructs a chronological timeline.",
    accent: "text-cyan",
    ring: "shadow-[0_0_40px_-10px_rgba(34,211,238,0.5)]",
  },
  {
    n: "03",
    emoji: "🎯",
    name: "BlameMapper",
    role: "Reason about causality",
    body: "Builds a directed causal graph from the evidence and isolates the single root cause with a calibrated confidence score.",
    accent: "text-mint",
    ring: "shadow-glow-mint",
  },
  {
    n: "04",
    emoji: "📝",
    name: "NarratorAgent",
    role: "Write the post-mortem",
    body: "Gemini 2.5 Flash authors a complete, production-grade post-mortem: impact, timeline, remediation steps and action items.",
    accent: "text-amber",
    ring: "shadow-[0_0_40px_-10px_rgba(245,166,35,0.5)]",
  },
];

export default function HowItWorks() {
  return (
    <section id="how" className="section spotlight">
      <Reveal className="mx-auto max-w-2xl text-center">
        <span className="eyebrow mb-5">How it works</span>
        <h2 className="font-display text-4xl font-bold tracking-tight text-white md:text-5xl">
          Four agents. One autonomous pipeline.
        </h2>
        <p className="mt-5 text-zinc-400">
          Each agent does a single job exceptionally well and hands structured state to the next —
          streaming every step to your screen in real time.
        </p>
      </Reveal>

      <div className="relative mt-16">
        {/* vertical spine */}
        <motion.div
          initial={{ scaleY: 0 }}
          whileInView={{ scaleY: 1 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 1.1, ease: "easeOut" }}
          className="absolute left-[27px] top-4 hidden h-[calc(100%-2rem)] w-px origin-top bg-gradient-to-b from-brand via-cyan to-amber md:block"
        />

        <div className="space-y-6">
          {AGENTS.map((a, i) => (
            <Reveal key={a.name} delay={i * 0.1}>
              <div className="group flex gap-5 md:gap-8">
                <div className="relative z-10 shrink-0">
                  <div
                    className={`grid h-14 w-14 place-items-center rounded-2xl border border-white/10 bg-ink-850 text-2xl ${a.ring} transition-transform duration-300 group-hover:scale-110`}
                  >
                    {a.emoji}
                  </div>
                </div>
                <div className="card flex-1 transition-transform duration-300 group-hover:-translate-y-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="font-mono text-xs text-zinc-600">{a.n}</span>
                    <h3 className="font-display text-lg font-semibold text-white">{a.name}</h3>
                    <span className={`text-xs font-semibold uppercase tracking-wider ${a.accent}`}>
                      {a.role}
                    </span>
                  </div>
                  <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-400">{a.body}</p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
