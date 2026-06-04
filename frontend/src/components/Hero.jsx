import { Suspense, lazy } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, Activity, Zap } from "lucide-react";

// Code-split the three.js scene so it never blocks first paint.
const NetworkField = lazy(() => import("../three/NetworkField.jsx"));

const STATS = [
  { value: "< 60s", label: "Alert → post-mortem" },
  { value: "94%", label: "Root-cause confidence" },
  { value: "4", label: "Autonomous agents" },
  { value: "0", label: "Humans paged" },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12, delayChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.21, 0.47, 0.32, 0.98] } },
};

export default function Hero() {
  return (
    <section id="top" className="relative min-h-screen overflow-hidden">
      {/* 3D network background */}
      <Suspense fallback={null}>
        <NetworkField className="absolute inset-0 -z-10 opacity-80" />
      </Suspense>

      {/* gradient + grid overlays */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid-faint bg-[size:64px_64px] [mask-image:radial-gradient(70%_60%_at_50%_30%,#000,transparent)]" />
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[60vh] bg-[radial-gradient(60%_50%_at_50%_0%,rgba(124,92,255,0.22),transparent_70%)]" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 -z-10 h-40 bg-gradient-to-t from-ink-950 to-transparent" />

      <div className="mx-auto flex max-w-5xl flex-col items-center px-6 pt-40 pb-24 text-center md:pt-48">
        <motion.div variants={container} initial="hidden" animate="show" className="flex flex-col items-center">
          <motion.div variants={item} className="eyebrow mb-7">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-mint opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-mint" />
            </span>
            Autonomous SRE · Dynatrace × Gemini 2.5 Flash
          </motion.div>

          <motion.h1
            variants={item}
            className="font-display text-5xl font-bold leading-[1.05] tracking-tight text-white md:text-7xl"
          >
            Your production dies at 3am.
            <br />
            <span className="gradient-text">SpecterOps wakes up</span> instead of you.
          </motion.h1>

          <motion.p
            variants={item}
            className="mt-7 max-w-2xl text-base leading-relaxed text-zinc-400 md:text-lg"
          >
            An autonomous, multi-agent forensics engine that takes a raw incident alert and
            returns a complete, evidence-backed post-mortem — root cause, causal graph and the
            exact fix — in under a minute. No human in the loop.
          </motion.p>

          <motion.div variants={item} className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
            <a href="#demo" className="btn-primary">
              <Zap className="h-4 w-4" /> Watch a live incident
            </a>
            <a href="#how" className="btn-ghost">
              See how it works
            </a>
          </motion.div>

          <motion.div variants={item} className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-zinc-500">
            <span className="inline-flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5 text-mint" /> Runs offline, zero accounts</span>
            <span className="inline-flex items-center gap-1.5"><Activity className="h-3.5 w-3.5 text-cyan" /> Real-time streaming analysis</span>
            <span className="inline-flex items-center gap-1.5"><Zap className="h-3.5 w-3.5 text-brand-soft" /> MIT-licensed open source</span>
          </motion.div>
        </motion.div>
      </div>

      {/* stat band */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.6 }}
        className="mx-auto -mb-px max-w-5xl px-6"
      >
        <div className="grid grid-cols-2 divide-x divide-white/10 overflow-hidden rounded-2xl border border-white/10 bg-ink-900/60 backdrop-blur-xl md:grid-cols-4">
          {STATS.map((s) => (
            <div key={s.label} className="px-6 py-6 text-center">
              <div className="font-display text-3xl font-bold text-white">{s.value}</div>
              <div className="mt-1 text-xs uppercase tracking-wider text-zinc-500">{s.label}</div>
            </div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
