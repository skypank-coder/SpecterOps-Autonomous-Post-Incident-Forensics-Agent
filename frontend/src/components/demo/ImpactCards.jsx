const fmtMs = (v) =>
  v == null ? "—" : v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${Math.round(v)}ms`;

export default function ImpactCards({ incident }) {
  const impact = incident?.impact;
  const dur = incident?.analysis_duration_seconds;
  const conf = incident?.root_cause_confidence;

  const cards = [
    impact?.error_rate_pct != null && {
      label: "Error rate",
      value: `${impact.error_rate_pct}%`,
      accent: "text-rose",
      sub: "peak",
    },
    impact?.p99_latency_ms != null && {
      label: "p99 latency",
      value: fmtMs(impact.p99_latency_ms),
      accent: "text-amber",
      sub: impact.baseline_latency_ms != null ? `baseline ${fmtMs(impact.baseline_latency_ms)}` : null,
    },
    impact?.latency_spike_ratio != null && {
      label: "Latency spike",
      value: `${impact.latency_spike_ratio}×`,
      accent: "text-brand-soft",
      sub: "vs baseline",
    },
    conf != null && {
      label: "RC confidence",
      value: `${conf}%`,
      accent: "text-mint",
      sub: null,
    },
    dur != null && {
      label: "Time to diagnose",
      value: `${dur}s`,
      accent: "text-cyan",
      sub: "autonomous",
    },
  ].filter(Boolean);

  if (cards.length === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map((c) => (
        <div key={c.label} className="rounded-xl border border-white/8 bg-white/[0.02] px-3 py-3">
          <div className="text-[9px] uppercase tracking-widest text-zinc-500">{c.label}</div>
          <div className={`mt-0.5 font-display text-xl font-bold ${c.accent}`}>{c.value}</div>
          {c.sub && <div className="text-[10px] text-zinc-600">{c.sub}</div>}
        </div>
      ))}
      {incident?.impact?.remediation_command && (
        <div className="col-span-2 flex items-center gap-2 rounded-xl border border-mint/20 bg-mint/[0.04] px-3 py-3 sm:col-span-3 lg:col-span-5">
          <span className="shrink-0 text-[9px] font-bold uppercase tracking-widest text-mint">
            Fix
          </span>
          <code className="truncate font-mono text-[11px] text-mint">
            {incident.impact.remediation_command}
          </code>
        </div>
      )}
    </div>
  );
}
