import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, Wand2, ChevronRight } from "lucide-react";
import DynatraceProblems from "./DynatraceProblems.jsx";

const SEV_COLOR = {
  CRITICAL: "text-rose",
  HIGH: "text-amber",
  MEDIUM: "text-cyan",
  LOW: "text-zinc-400",
};

export default function IncidentLauncher({
  scenarios,
  onRun,
  onRunCustom,
  onRunDynatrace,
  dynatraceConnected,
  busy,
}) {
  const [showCustom, setShowCustom] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [services, setServices] = useState("");
  const [severity, setSeverity] = useState("HIGH");

  function submitCustom(e) {
    e.preventDefault();
    if (!title.trim()) return;
    onRunCustom({
      title: title.trim(),
      description: description.trim(),
      services: services.split(",").map((s) => s.trim()).filter(Boolean),
      severity,
    });
  }

  return (
    <div className="space-y-5">
      <div className="text-center">
        <div className="mb-3 text-5xl">👻</div>
        <h3 className="font-display text-xl font-bold text-white">Launch an investigation</h3>
        <p className="mx-auto mt-1 max-w-md text-sm text-zinc-400">
          Pick a real-world incident scenario and watch the four agents diagnose it live — or
          describe your own.
        </p>
      </div>

      {/* live Dynatrace — browse & pick a real open problem */}
      <DynatraceProblems connected={dynatraceConnected} onRun={onRunDynatrace} busy={busy} />

      {dynatraceConnected && (
        <div className="flex items-center gap-3">
          <span className="h-px flex-1 bg-white/8" />
          <span className="text-[10px] uppercase tracking-widest text-zinc-600">or replay a scenario</span>
          <span className="h-px flex-1 bg-white/8" />
        </div>
      )}

      {/* scenario grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {scenarios.map((s) => (
          <button
            key={s.id}
            disabled={busy}
            onClick={() => onRun(s.id)}
            className="group flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4 text-left transition-all hover:-translate-y-0.5 hover:border-brand/40 hover:bg-white/[0.04] disabled:opacity-50"
          >
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-white/10 bg-ink-850 text-xl">
              {s.emoji}
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-2">
                <span className="truncate font-display text-sm font-semibold text-white">
                  {s.name}
                </span>
                <span className={`text-[10px] font-bold ${SEV_COLOR[s.severity] || "text-zinc-400"}`}>
                  {s.severity}
                </span>
              </span>
              <span className="mt-0.5 block truncate text-xs text-zinc-500">
                {s.primary_service} · {s.services.length} services
              </span>
            </span>
            <ChevronRight className="h-4 w-4 shrink-0 text-zinc-600 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-soft" />
          </button>
        ))}
      </div>

      {/* custom toggle */}
      <button
        onClick={() => setShowCustom((v) => !v)}
        className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-white/15 bg-white/[0.01] py-3 text-sm font-semibold text-zinc-300 transition-colors hover:border-brand/40 hover:text-white"
      >
        <Wand2 className="h-4 w-4 text-brand-soft" />
        {showCustom ? "Hide custom incident" : "Describe your own incident"}
      </button>

      <AnimatePresence>
        {showCustom && (
          <motion.form
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            onSubmit={submitCustom}
            className="space-y-3 overflow-hidden rounded-xl border border-white/10 bg-white/[0.02] p-4"
          >
            <div>
              <label className="mb-1 block text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                Incident title *
              </label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Redis evictions causing session loss in auth-service"
                className="w-full rounded-lg border border-white/10 bg-ink-950/60 px-3 py-2.5 text-sm text-white placeholder-zinc-600 outline-none focus:border-brand/50"
              />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                What's happening?
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Describe the symptoms, recent changes, error messages…"
                className="w-full resize-none rounded-lg border border-white/10 bg-ink-950/60 px-3 py-2.5 text-sm text-white placeholder-zinc-600 outline-none focus:border-brand/50"
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                  Affected services
                </label>
                <input
                  value={services}
                  onChange={(e) => setServices(e.target.value)}
                  placeholder="auth-service, api-gateway"
                  className="w-full rounded-lg border border-white/10 bg-ink-950/60 px-3 py-2.5 text-sm text-white placeholder-zinc-600 outline-none focus:border-brand/50"
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                  Severity
                </label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-ink-950/60 px-3 py-2.5 text-sm text-white outline-none focus:border-brand/50"
                >
                  {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((s) => (
                    <option key={s} value={s} className="bg-ink-850">
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <button type="submit" disabled={busy || !title.trim()} className="btn-primary w-full">
              <Zap className="h-4 w-4" /> Investigate this incident
            </button>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}
