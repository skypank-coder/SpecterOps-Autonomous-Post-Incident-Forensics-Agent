import { Zap } from "lucide-react";
import Reveal from "./Reveal.jsx";

export default function CTA() {
  return (
    <section className="section">
      <Reveal>
        <div className="border-glow relative overflow-hidden rounded-3xl border border-white/10 bg-ink-900/70 px-6 py-20 text-center backdrop-blur-xl">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_80%_at_50%_0%,rgba(124,92,255,0.22),transparent_70%)]" />
          <div className="pointer-events-none absolute inset-0 bg-grid-faint bg-[size:48px_48px] [mask-image:radial-gradient(60%_60%_at_50%_40%,#000,transparent)]" />
          <div className="relative mx-auto max-w-2xl">
            <div className="mb-6 text-5xl">👻</div>
            <h2 className="font-display text-4xl font-bold leading-tight tracking-tight text-white md:text-5xl">
              Stop debugging at 3am.
              <br />
              <span className="gradient-text">Let the ghost do it.</span>
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-zinc-400">
              See SpecterOps trace a live cascading outage to its root cause — and write the
              post-mortem — before you could finish reading the alert.
            </p>
            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <a href="#demo" className="btn-primary">
                <Zap className="h-4 w-4" /> Launch the live demo
              </a>
              <a
                href="https://github.com/skypank-coder/SpecterOps-Autonomous-Post-Incident-Forensics-Agent"
                target="_blank"
                rel="noreferrer"
                className="btn-ghost"
              >
                Star on GitHub
              </a>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
