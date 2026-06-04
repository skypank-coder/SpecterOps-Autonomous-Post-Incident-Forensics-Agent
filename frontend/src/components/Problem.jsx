import { Moon, Search, Clock, Flame } from "lucide-react";
import Reveal from "./Reveal.jsx";

const PAINS = [
  {
    icon: Moon,
    title: "It always happens at 3am",
    body: "An on-call engineer gets paged, half-asleep, into a cascading outage they've never seen before.",
  },
  {
    icon: Search,
    title: "An hour of frantic pivoting",
    body: "Tab after tab — traces, logs, metrics, dashboards — manually correlating signals under pressure.",
  },
  {
    icon: Clock,
    title: "MTTR bleeds revenue",
    body: "Every minute the root cause stays hidden, errors compound and customers churn.",
  },
  {
    icon: Flame,
    title: "The post-mortem never gets written",
    body: "Once the fire is out, nobody documents it — so the same class of incident happens again.",
  },
];

export default function Problem() {
  return (
    <section className="section">
      <div className="grid items-start gap-14 lg:grid-cols-[0.9fr_1.1fr]">
        <Reveal>
          <span className="eyebrow mb-5">The 3am problem</span>
          <h2 className="font-display text-4xl font-bold leading-tight tracking-tight text-white md:text-5xl">
            Incident response is still painfully{" "}
            <span className="text-rose">manual</span>.
          </h2>
          <p className="mt-6 max-w-md text-zinc-400">
            Observability tools are great at telling you <em>something is wrong</em>. They are
            terrible at telling you <em>why</em>, <em>how it cascaded</em>, and <em>what to do</em>{" "}
            — fast enough to matter. That last mile is still done by exhausted humans.
          </p>
          <p className="mt-4 max-w-md text-zinc-400">
            SpecterOps automates the entire forensic investigation, so the answer is waiting for
            you before you've even opened your laptop.
          </p>
        </Reveal>

        <div className="grid gap-4 sm:grid-cols-2">
          {PAINS.map((p, i) => (
            <Reveal key={p.title} delay={i * 0.08}>
              <div className="card h-full transition-transform duration-300 hover:-translate-y-1">
                <div className="mb-4 grid h-11 w-11 place-items-center rounded-xl border border-white/10 bg-white/[0.04] text-rose">
                  <p.icon className="h-5 w-5" />
                </div>
                <h3 className="font-display text-base font-semibold text-white">{p.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-400">{p.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
