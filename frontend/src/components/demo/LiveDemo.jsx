import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw, Lock } from "lucide-react";
import { API_BASE } from "../../lib/api.js";
import { useAuth } from "../../context/AuthContext.jsx";
import Reveal from "../Reveal.jsx";
import AgentPipeline from "./AgentPipeline.jsx";
import CausalGraph from "./CausalGraph.jsx";
import PostMortem from "./PostMortem.jsx";
import ImpactCards from "./ImpactCards.jsx";
import IncidentLauncher from "./IncidentLauncher.jsx";
import IncidentSwitcher from "./IncidentSwitcher.jsx";
import StatusBadges from "./StatusBadges.jsx";

const STATUS_META = {
  DETECTING: { label: "Detecting", cls: "text-cyan border-cyan/40 bg-cyan/10", live: true },
  ANALYZING: { label: "Analyzing", cls: "text-amber border-amber/40 bg-amber/10", live: true },
  ROOT_CAUSE_FOUND: { label: "Root cause found", cls: "text-brand-soft border-brand/40 bg-brand/10", live: true },
  WRITING_POSTMORTEM: { label: "Writing post-mortem", cls: "text-amber border-amber/40 bg-amber/10", live: true },
  COMPLETE: { label: "Complete", cls: "text-mint border-mint/40 bg-mint/10", live: false },
  FAILED: { label: "Failed", cls: "text-rose border-rose/40 bg-rose/10", live: false },
};

const SEV = { CRITICAL: "text-rose", HIGH: "text-amber", MEDIUM: "text-cyan", LOW: "text-zinc-500" };

export default function LiveDemo() {
  const { user, openSignIn } = useAuth();
  const owner = user ? user.email || user.uid : null;
  const [notice, setNotice] = useState(null);

  const [config, setConfig] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [view, setView] = useState("launcher"); // 'launcher' | 'incident'
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [tab, setTab] = useState("graph");
  const esRef = useRef(null);

  const incident = incidents.find((i) => i.id === activeId) || null;

  useEffect(() => {
    fetch(`${API_BASE}/api/config`).then((r) => r.json()).then(setConfig).catch(() => {});
    fetch(`${API_BASE}/api/scenarios`).then((r) => r.json()).then(setScenarios).catch(() => {});
    return () => esRef.current?.close();
  }, []);

  const loadIncidents = useCallback(() => {
    const url = owner
      ? `${API_BASE}/api/incidents/?owner=${encodeURIComponent(owner)}`
      : `${API_BASE}/api/incidents/`;
    fetch(url)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length) {
          setIncidents(data);
          setActiveId((cur) => cur || data[0].id);
          setView((v) => (v === "launcher" && !isAnalyzing ? "incident" : v));
        }
      })
      .catch(() => {});
  }, [owner]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  function upsert(updated) {
    setIncidents((prev) => {
      const idx = prev.findIndex((i) => i.id === updated.id);
      if (idx === -1) return [updated, ...prev];
      const next = [...prev];
      next[idx] = updated;
      return next;
    });
  }

  function openStream(incidentId) {
    esRef.current?.close();
    const es = new EventSource(`${API_BASE}/api/stream/${incidentId}`);
    esRef.current = es;
    es.onmessage = (event) => {
      let p;
      try {
        p = JSON.parse(event.data);
      } catch {
        return;
      }
      if (p.type === "heartbeat") return;
      if (p.incident) upsert(p.incident);
      if (p.status === "COMPLETE" || p.status === "FAILED") {
        setIsAnalyzing(false);
        es.close();
      }
    };
    es.onerror = () => {
      setIsAnalyzing(false);
      es.close();
    };
  }

  async function runScenario(scenarioId) {
    setIsAnalyzing(true);
    setView("incident");
    setTab("graph");
    try {
      const res = await fetch(`${API_BASE}/api/incidents/demo/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_id: scenarioId, owner }),
      });
      const { incident_id } = await res.json();
      setActiveId(incident_id);
      openStream(incident_id);
    } catch {
      setIsAnalyzing(false);
    }
  }

  async function runCustom(payload) {
    setIsAnalyzing(true);
    setView("incident");
    setTab("graph");
    try {
      const res = await fetch(`${API_BASE}/api/incidents/custom/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, owner }),
      });
      const { incident_id } = await res.json();
      setActiveId(incident_id);
      openStream(incident_id);
    } catch {
      setIsAnalyzing(false);
    }
  }

  async function runDynatrace() {
    setNotice(null);
    setIsAnalyzing(true);
    setView("incident");
    setTab("graph");
    try {
      const res = await fetch(`${API_BASE}/api/incidents/dynatrace/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ owner }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setNotice(err.detail || "Could not reach Dynatrace.");
        setIsAnalyzing(false);
        setView("launcher");
        return;
      }
      const { incident_id } = await res.json();
      setActiveId(incident_id);
      openStream(incident_id);
    } catch {
      setNotice("Could not reach Dynatrace.");
      setIsAnalyzing(false);
      setView("launcher");
    }
  }

  async function resetActive() {
    if (incident?.id) {
      try {
        await fetch(`${API_BASE}/api/incidents/${incident.id}`, { method: "DELETE" });
      } catch {}
    }
    esRef.current?.close();
    setIncidents((prev) => {
      const next = prev.filter((i) => i.id !== incident?.id);
      setActiveId(next[0]?.id || null);
      setView(next.length ? "incident" : "launcher");
      return next;
    });
  }

  const meta = STATUS_META[incident?.status] || null;
  const showLauncher = view === "launcher" || !incident;

  return (
    <section id="demo" className="section spotlight">
      <Reveal className="mx-auto max-w-2xl text-center">
        <span className="eyebrow mb-5">Live incident console</span>
        <h2 className="font-display text-4xl font-bold tracking-tight text-white md:text-5xl">
          Real incidents, diagnosed in{" "}
          <span className="gradient-text">real time</span>.
        </h2>
        <p className="mt-5 text-zinc-400">
          Pull a live open problem straight from Dynatrace, replay a real-world failure scenario, or
          describe your own — and watch four agents reason to the root cause with Gemini, autonomously.
        </p>
      </Reveal>

      <Reveal delay={0.1} className="mt-12">
        <div className="border-glow overflow-hidden rounded-2xl border border-white/10 bg-ink-900/70 shadow-card backdrop-blur-xl">
          {/* window chrome */}
          <div className="flex flex-wrap items-center gap-3 border-b border-white/10 bg-ink-950/60 px-4 py-3">
            <div className="flex gap-1.5">
              <span className="h-3 w-3 rounded-full bg-rose/70" />
              <span className="h-3 w-3 rounded-full bg-amber/70" />
              <span className="h-3 w-3 rounded-full bg-mint/70" />
            </div>
            <span className="font-mono text-xs text-zinc-500">specterops — incident console</span>
            {!showLauncher && meta && (
              <span
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${meta.cls}`}
              >
                {meta.live && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
                {meta.label}
              </span>
            )}
            <div className="ml-auto">
              <StatusBadges config={config} />
            </div>
          </div>

          {/* body */}
          <div className="p-5">
            {!user ? (
              <div className="grid place-items-center px-6 py-20 text-center">
                <div className="mb-5 grid h-14 w-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.03] text-brand-soft">
                  <Lock className="h-6 w-6" />
                </div>
                <h3 className="font-display text-xl font-bold text-white">
                  Sign in to launch the console
                </h3>
                <p className="mt-2 max-w-md text-sm text-zinc-400">
                  Investigations run under your account so your post-mortems and history are saved to
                  your workspace. It's free — Google or email, one click.
                </p>
                <button onClick={openSignIn} className="btn-primary mt-7">
                  Sign in to continue
                </button>
              </div>
            ) : showLauncher ? (
              <div className="px-2 py-6">
                {notice && (
                  <div className="mb-4 rounded-xl border border-amber/30 bg-amber/10 px-4 py-3 text-center text-xs text-amber">
                    {notice}
                  </div>
                )}
                <IncidentLauncher
                  scenarios={scenarios}
                  onRun={runScenario}
                  onRunCustom={runCustom}
                  onRunDynatrace={runDynatrace}
                  dynatraceConnected={Boolean(config?.dynatrace?.connected)}
                  busy={isAnalyzing}
                />
                {incidents.length > 0 && (
                  <div className="mt-6 border-t border-white/8 pt-4">
                    <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                      Recent investigations
                    </p>
                    <IncidentSwitcher
                      incidents={incidents}
                      activeId={activeId}
                      onSelect={(id) => {
                        setActiveId(id);
                        setView("incident");
                      }}
                      onNew={() => {}}
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-5">
                <div className="flex items-center justify-between gap-3">
                  <IncidentSwitcher
                    incidents={incidents}
                    activeId={activeId}
                    onSelect={setActiveId}
                    onNew={() => setView("launcher")}
                  />
                  {!isAnalyzing && (
                    <button
                      onClick={resetActive}
                      className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-white/15 px-3 py-2 text-xs font-semibold text-zinc-400 transition-colors hover:border-rose/40 hover:text-rose"
                    >
                      <RotateCcw className="h-3.5 w-3.5" /> Delete
                    </button>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <span className={`text-xs font-bold uppercase tracking-wider ${SEV[incident.severity] || "text-zinc-400"}`}>
                    [{incident.severity}]
                  </span>
                  <h3 className="font-display text-base font-semibold text-white">{incident.title}</h3>
                  <span className="text-xs text-zinc-500">
                    {(incident.affected_services || []).join(" · ")}
                  </span>
                </div>

                <ImpactCards incident={incident} />

                <div className="grid gap-5 lg:grid-cols-12">
                  <div className="lg:col-span-5">
                    <AgentPipeline incident={incident} isAnalyzing={isAnalyzing} />
                  </div>
                  <div className="lg:col-span-7">
                    <div className="mb-3 flex gap-1 rounded-xl border border-white/10 bg-white/[0.02] p-1">
                      {[
                        { id: "graph", label: "Causal graph" },
                        { id: "postmortem", label: "Post-mortem" },
                      ].map((t) => (
                        <button
                          key={t.id}
                          onClick={() => setTab(t.id)}
                          className={`flex-1 rounded-lg px-4 py-2 text-xs font-semibold transition-colors ${
                            tab === t.id ? "bg-white/[0.06] text-white" : "text-zinc-500 hover:text-zinc-300"
                          }`}
                        >
                          {t.label}
                        </button>
                      ))}
                    </div>
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={tab}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        transition={{ duration: 0.25 }}
                      >
                        {tab === "graph" ? (
                          <CausalGraph incident={incident} />
                        ) : (
                          <PostMortem
                            incident={incident}
                            slackConnected={Boolean(config?.slack?.connected)}
                            dynatraceConnected={Boolean(config?.dynatrace?.connected)}
                          />
                        )}
                      </motion.div>
                    </AnimatePresence>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </Reveal>
    </section>
  );
}
