import { useEffect, useRef, useState } from "react";
import { useInView } from "framer-motion";
import Reveal from "./Reveal.jsx";

function Counter({ to, decimals = 0, prefix = "", suffix = "", duration = 1600 }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const [val, setVal] = useState(0);

  useEffect(() => {
    if (!inView) return;
    let raf;
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setVal(to * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, to, duration]);

  return (
    <span ref={ref}>
      {prefix}
      {val.toFixed(decimals)}
      {suffix}
    </span>
  );
}

const METRICS = [
  { node: <Counter to={45} suffix="s" />, label: "Median time to full post-mortem", accent: "text-cyan" },
  { node: <Counter to={94} suffix="%" />, label: "Root-cause confidence", accent: "text-mint" },
  { node: <Counter to={34} suffix="%" />, label: "Error rate traced to one index", accent: "text-rose" },
  { node: <Counter to={4.2} decimals={1} suffix="s" />, label: "p99 latency at peak", accent: "text-amber" },
];

export default function Metrics() {
  return (
    <section id="impact" className="relative overflow-hidden border-y border-white/5 bg-ink-950/70 py-24">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(50%_60%_at_50%_50%,rgba(124,92,255,0.12),transparent_70%)]" />
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="eyebrow mb-5">Impact</span>
          <h2 className="font-display text-4xl font-bold tracking-tight text-white md:text-5xl">
            The numbers behind the demo.
          </h2>
          <p className="mt-5 text-zinc-400">
            A single missing index took down a payment pipeline. Here's what SpecterOps surfaced —
            autonomously.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-2 gap-6 lg:grid-cols-4">
          {METRICS.map((m, i) => (
            <Reveal key={m.label} delay={i * 0.1}>
              <div className="card text-center">
                <div className={`font-display text-5xl font-bold ${m.accent}`}>{m.node}</div>
                <div className="mt-3 text-xs uppercase tracking-wider text-zinc-500">
                  {m.label}
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
