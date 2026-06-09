import { useCallback, useEffect, useState } from "react";
import { Radio, RefreshCw, ChevronRight, Loader2 } from "lucide-react";
import { API_BASE } from "../../lib/api.js";

const SEV_DOT = {
  CRITICAL: "bg-rose",
  HIGH: "bg-amber",
  MEDIUM: "bg-cyan",
  LOW: "bg-zinc-500",
};
const SEV_TEXT = {
  CRITICAL: "text-rose",
  HIGH: "text-amber",
  MEDIUM: "text-cyan",
  LOW: "text-zinc-400",
};

function ago(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const mins = Math.max(0, Math.round((Date.now() - d.getTime()) / 60000));
  if (mins < 60) return `${mins}m ago`;
  const h = Math.floor(mins / 60);
  return `${h}h ${mins % 60}m ago`;
}

export default function DynatraceProblems({ connected, onRun, busy }) {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    if (!connected) return;
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/api/dynatrace/problems`)
      .then((r) => r.json())
      .then((d) => {
        setProblems(Array.isArray(d.problems) ? d.problems : []);
        if (d.error) setError(d.error);
      })
      .catch(() => setError("Could not reach Dynatrace."))
      .finally(() => setLoading(false));
  }, [connected]);

  useEffect(() => {
    load();
  }, [load]);

  if (!connected) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-dashed border-white/10 bg-white/[0.01] p-3 text-xs text-zinc-500">
        <Radio className="h-4 w-4 shrink-0" />
        <span>
          Connect a live Dynatrace tenant (set <code className="text-zinc-400">DYNATRACE_*</code> and{" "}
          <code className="text-zinc-400">DEMO_MODE=false</code>) to browse and investigate real
          open problems.
        </span>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-brand/25 bg-brand/[0.04] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-brand-soft" />
          <span className="font-display text-sm font-semibold text-white">
            Live Dynatrace problems
          </span>
          <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[10px] text-zinc-400">
            {problems.length} open
          </span>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-white/15 px-2.5 py-1.5 text-[11px] font-semibold text-zinc-300 transition-colors hover:border-brand/40 hover:text-brand-soft"
        >
          {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
          Refresh
        </button>
      </div>

      {error && (
        <p className="mb-2 rounded-lg border border-amber/30 bg-amber/10 px-3 py-2 text-[11px] text-amber">
          {error}
        </p>
      )}

      {loading && problems.length === 0 ? (
        <p className="py-4 text-center text-xs text-zinc-500">Loading open problems…</p>
      ) : problems.length === 0 ? (
        <p className="py-4 text-center text-xs text-zinc-500">
          No open problems in your tenant right now. 🎉
        </p>
      ) : (
        <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
          {problems.map((p) => (
            <button
              key={p.id}
              disabled={busy}
              onClick={() => onRun(p.id)}
              className="group flex w-full items-center gap-3 rounded-lg border border-white/10 bg-ink-950/40 p-3 text-left transition-all hover:-translate-y-0.5 hover:border-brand/40 disabled:opacity-50"
            >
              <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${SEV_DOT[p.severity] || "bg-zinc-500"}`} />
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-2">
                  <span className={`text-[10px] font-bold ${SEV_TEXT[p.severity] || "text-zinc-400"}`}>
                    {p.severity}
                  </span>
                  <span className="truncate text-sm font-medium text-white">{p.title}</span>
                </span>
                <span className="mt-0.5 block truncate text-[11px] text-zinc-500">
                  {(p.services || []).join(", ") || "—"}
                  {p.start_time ? ` · ${ago(p.start_time)}` : ""}
                </span>
              </span>
              <span className="inline-flex shrink-0 items-center gap-1 rounded-md bg-brand/15 px-2 py-1 text-[10px] font-bold text-brand-soft opacity-0 transition-opacity group-hover:opacity-100">
                Investigate <ChevronRight className="h-3 w-3" />
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
