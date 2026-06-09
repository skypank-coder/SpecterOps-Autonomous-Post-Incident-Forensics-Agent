import { Database, FileText, Activity, Network, Fingerprint } from "lucide-react";

const LEVEL = {
  ERROR: "text-rose",
  WARN: "text-amber",
  INFO: "text-cyan",
};

function fmtTime(ts) {
  try {
    return new Date(ts).toLocaleTimeString("en-US", { hour12: false });
  } catch {
    return "--:--:--";
  }
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2">
      <Icon className="h-4 w-4 text-brand-soft" />
      <div className="leading-tight">
        <div className="font-display text-sm font-bold text-white">{value}</div>
        <div className="text-[9px] uppercase tracking-wider text-zinc-500">{label}</div>
      </div>
    </div>
  );
}

export default function EvidencePanel({ incident }) {
  const raw = incident?.raw_data || {};
  const logs = raw.logs?.results || [];
  const traceSummary = raw.trace_summary || {};
  const metricSummary = raw.metric_summary || {};
  const topo = raw.topology?.entities?.[0] || {};
  const badTags = traceSummary.sample_bad_span_tags || {};
  const scenarioEvidence = raw.scenario?.evidence || [];

  const rt = metricSummary["builtin:service.response.time"];
  const err = metricSummary["builtin:service.errors.total.rate"];

  const hasAnything =
    logs.length || Object.keys(badTags).length || scenarioEvidence.length || rt || err;

  if (!hasAnything) {
    return (
      <div className="grid h-[420px] place-items-center text-center text-sm text-zinc-500">
        Evidence is captured during a live investigation — run one to inspect the raw signals.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* signals analyzed */}
      <div>
        <h4 className="mb-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
          Signals analyzed
        </h4>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat icon={Database} label="Traces" value={traceSummary.count ?? "—"} />
          <Stat icon={FileText} label="Log lines" value={logs.length || "—"} />
          <Stat icon={Activity} label="Metrics" value={Object.keys(metricSummary).length || "—"} />
          <Stat
            icon={Network}
            label="Topology"
            value={(topo.calls?.length || 0) + (topo.calledBy?.length || 0) || "—"}
          />
        </div>
      </div>

      {/* decisive evidence */}
      <div>
        <h4 className="mb-2 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-mint">
          <Fingerprint className="h-3.5 w-3.5" /> Decisive evidence
        </h4>
        <div className="space-y-2 rounded-xl border border-mint/20 bg-mint/[0.04] p-3">
          {badTags["db.index_hit"] === "false" && (
            <div className="font-mono text-xs text-zinc-300">
              <span className="text-mint">db.index_hit</span> = "false" ·{" "}
              <span className="text-mint">db.rows_examined</span> ={" "}
              {Number(badTags["db.rows_examined"]).toLocaleString()} ·{" "}
              <span className="text-mint">db.table</span> = {badTags["db.table"]}
              <div className="mt-1 text-[11px] text-zinc-500">{badTags["db.statement"]}</div>
            </div>
          )}
          {scenarioEvidence.slice(0, 5).map((e, i) => (
            <div key={i} className="text-xs text-zinc-300">
              • {e}
            </div>
          ))}
          {!badTags["db.index_hit"] && scenarioEvidence.length === 0 && (
            <div className="text-xs text-zinc-500">
              Root cause inferred from the metric shift and log sequence below.
            </div>
          )}
        </div>
      </div>

      {/* metric shift */}
      {(rt || err) && (
        <div>
          <h4 className="mb-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
            Metric shift (baseline → peak)
          </h4>
          <div className="overflow-hidden rounded-xl border border-white/8">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-white/[0.02] text-[10px] uppercase tracking-wider text-zinc-500">
                  <th className="px-3 py-2 text-left">Metric</th>
                  <th className="px-3 py-2 text-right">Baseline</th>
                  <th className="px-3 py-2 text-right">Peak</th>
                  <th className="px-3 py-2 text-right">Spike</th>
                </tr>
              </thead>
              <tbody className="text-zinc-300">
                {rt && (
                  <tr className="border-t border-white/8">
                    <td className="px-3 py-2">Response time</td>
                    <td className="px-3 py-2 text-right">{rt.min}</td>
                    <td className="px-3 py-2 text-right text-amber">{rt.max}</td>
                    <td className="px-3 py-2 text-right text-brand-soft">{rt.spike_ratio}×</td>
                  </tr>
                )}
                {err && (
                  <tr className="border-t border-white/8">
                    <td className="px-3 py-2">Error rate</td>
                    <td className="px-3 py-2 text-right">{err.min}</td>
                    <td className="px-3 py-2 text-right text-rose">{err.max}</td>
                    <td className="px-3 py-2 text-right text-brand-soft">{err.spike_ratio}×</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* signal log */}
      {logs.length > 0 && (
        <div>
          <h4 className="mb-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
            Signal log ({logs.length})
          </h4>
          <div className="max-h-64 space-y-1 overflow-y-auto rounded-xl border border-white/8 bg-ink-950/40 p-2 font-mono text-[11px]">
            {logs.map((l, i) => (
              <div key={i} className="flex gap-2 px-1 py-0.5">
                <span className="shrink-0 text-zinc-600">{fmtTime(l.timestamp)}</span>
                <span className={`shrink-0 font-bold ${LEVEL[l.level] || "text-zinc-400"}`}>
                  {(l.level || "").padEnd(5)}
                </span>
                <span className="shrink-0 text-brand-soft">{l.service}</span>
                <span className="text-zinc-400">{l.content}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
