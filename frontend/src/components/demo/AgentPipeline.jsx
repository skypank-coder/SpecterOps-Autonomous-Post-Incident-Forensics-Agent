import { motion } from "framer-motion";

const AGENTS = [
  { name: "SentinelAgent", emoji: "🛡️", desc: "Classifying the alert & extracting targets" },
  { name: "TraceArchaeologist", emoji: "🔍", desc: "Querying traces · logs · metrics · topology" },
  { name: "BlameMapper", emoji: "🎯", desc: "Building the causal graph & root cause" },
  { name: "NarratorAgent", emoji: "📝", desc: "Writing the post-mortem with Gemini" },
];

const SEV = {
  CRITICAL: "text-rose",
  HIGH: "text-amber",
  MEDIUM: "text-cyan",
  LOW: "text-zinc-500",
};

function fmtTime(ts) {
  try {
    return new Date(ts).toLocaleTimeString("en-US", { hour12: false });
  } catch {
    return "--:--:--";
  }
}

export default function AgentPipeline({ incident, isAnalyzing }) {
  const steps = incident?.agent_steps || [];
  const byName = {};
  steps.forEach((s) => (byName[s.agent_name] = s));
  const completed = AGENTS.filter((a) => byName[a.name]).length;
  const active = ["COMPLETE", "FAILED"].includes(incident?.status) ? -1 : completed;

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        {AGENTS.map((a, i) => {
          const step = byName[a.name];
          const done = Boolean(step);
          const isActive = i === active;
          return (
            <motion.div
              key={a.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`flex gap-3 rounded-xl border p-3 transition-colors ${
                done
                  ? "border-mint/25 bg-mint/[0.04]"
                  : isActive
                  ? "border-amber/40 bg-amber/[0.05]"
                  : "border-white/8 bg-white/[0.02]"
              }`}
            >
              <div
                className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg border text-base ${
                  done
                    ? "border-mint/40 bg-mint/10"
                    : isActive
                    ? "border-amber/50 bg-amber/10"
                    : "border-white/10 bg-white/[0.03]"
                }`}
              >
                {a.emoji}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-sm font-semibold ${
                      done ? "text-mint" : isActive ? "text-amber" : "text-zinc-400"
                    }`}
                  >
                    {a.name}
                  </span>
                  {isActive && (
                    <span className="flex gap-1">
                      {[0, 1, 2].map((d) => (
                        <motion.span
                          key={d}
                          className="h-1 w-1 rounded-full bg-amber"
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ duration: 1, repeat: Infinity, delay: d * 0.2 }}
                        />
                      ))}
                    </span>
                  )}
                  {done && <span className="ml-auto text-xs text-mint">✓</span>}
                </div>
                <p className="mt-0.5 truncate text-xs text-zinc-500">
                  {done ? step.result : a.desc}
                </p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {incident?.timeline?.length > 0 && (
        <div>
          <h4 className="mb-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
            Reconstructed timeline · {incident.timeline.length} events
          </h4>
          <div className="space-y-1.5">
            {incident.timeline.map((ev, i) => (
              <div
                key={i}
                className={`flex items-start gap-2.5 rounded-lg border px-3 py-2 text-xs ${
                  ev.is_root_cause_candidate
                    ? "border-rose/30 bg-rose/[0.07]"
                    : "border-white/8 bg-white/[0.02]"
                }`}
              >
                <span className="mt-0.5 w-14 shrink-0 font-mono text-[10px] text-zinc-600">
                  {fmtTime(ev.timestamp)}
                </span>
                <span className="mt-0.5 w-28 shrink-0 truncate font-medium text-brand-soft">
                  {ev.service}
                </span>
                <span className="flex-1 text-zinc-400">{ev.description}</span>
                <span className={`shrink-0 font-bold ${SEV[ev.severity] || "text-zinc-500"}`}>
                  {ev.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
