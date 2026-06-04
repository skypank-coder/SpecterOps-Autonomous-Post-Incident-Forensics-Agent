import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, LogOut, ShieldCheck } from "lucide-react";
import { useAuth } from "../../context/AuthContext.jsx";
import { API_BASE } from "../../lib/api.js";

function Avatar({ user, size = "h-16 w-16 text-2xl" }) {
  const initial = (user.displayName || user.email || "U").charAt(0).toUpperCase();
  if (user.photoURL) return <img src={user.photoURL} alt="" className={`${size} rounded-2xl`} />;
  return (
    <span className={`grid ${size} place-items-center rounded-2xl bg-gradient-to-br from-brand to-brand-soft font-bold text-white`}>
      {initial}
    </span>
  );
}

export default function ProfileModal({ open, onClose }) {
  const { user, mode, signOutUser } = useAuth();
  const [incidents, setIncidents] = useState([]);

  const owner = user ? user.email || user.uid : null;

  useEffect(() => {
    if (!open || !owner) return;
    fetch(`${API_BASE}/api/incidents/?owner=${encodeURIComponent(owner)}`)
      .then((r) => r.json())
      .then((d) => setIncidents(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, [open, owner]);

  if (!user) return null;

  const total = incidents.length;
  const resolved = incidents.filter((i) => i.status === "COMPLETE").length;
  const avgConf =
    resolved > 0
      ? Math.round(
          incidents
            .filter((i) => i.root_cause_confidence)
            .reduce((a, i) => a + i.root_cause_confidence, 0) /
            Math.max(1, incidents.filter((i) => i.root_cause_confidence).length)
        )
      : 0;

  const stats = [
    { label: "Investigations", value: total },
    { label: "Resolved", value: resolved },
    { label: "Avg confidence", value: avgConf ? `${avgConf}%` : "—" },
  ];

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-ink-950/80 backdrop-blur-sm" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.25 }}
            className="border-glow relative w-full max-w-lg overflow-hidden rounded-2xl border border-white/10 bg-ink-900/90 p-7 shadow-card backdrop-blur-xl"
          >
            <button
              onClick={onClose}
              className="absolute right-4 top-4 grid h-8 w-8 place-items-center rounded-lg text-zinc-500 transition-colors hover:bg-white/5 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="flex items-center gap-4">
              <Avatar user={user} />
              <div className="min-w-0">
                <h3 className="truncate font-display text-xl font-bold text-white">
                  {user.displayName}
                </h3>
                <p className="truncate text-sm text-zinc-500">{user.email}</p>
                <span className="mt-1 inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[10px] font-medium text-zinc-400">
                  <ShieldCheck className="h-3 w-3 text-mint" />
                  {mode === "firebase" ? "Firebase account" : "Demo account"}
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-3 gap-3">
              {stats.map((s) => (
                <div key={s.label} className="rounded-xl border border-white/8 bg-white/[0.02] px-3 py-4 text-center">
                  <div className="font-display text-2xl font-bold text-white">{s.value}</div>
                  <div className="mt-1 text-[10px] uppercase tracking-wider text-zinc-500">{s.label}</div>
                </div>
              ))}
            </div>

            <div className="mt-6">
              <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                Recent investigations
              </p>
              <div className="max-h-48 space-y-1.5 overflow-y-auto pr-1">
                {incidents.length === 0 && (
                  <p className="rounded-lg border border-white/8 bg-white/[0.02] px-3 py-3 text-xs text-zinc-500">
                    No investigations yet — launch one from the live demo.
                  </p>
                )}
                {incidents.map((i) => (
                  <div
                    key={i.id}
                    className="flex items-center gap-2 rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2"
                  >
                    <span
                      className={`h-2 w-2 shrink-0 rounded-full ${
                        i.status === "COMPLETE" ? "bg-mint" : i.status === "FAILED" ? "bg-rose" : "bg-amber"
                      }`}
                    />
                    <span className="flex-1 truncate text-xs text-zinc-300">{i.title}</span>
                    {i.root_cause_confidence != null && (
                      <span className="shrink-0 text-[10px] font-semibold text-mint">
                        {i.root_cause_confidence}%
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => {
                onClose();
                signOutUser();
              }}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl border border-white/15 px-4 py-3 text-sm font-semibold text-zinc-300 transition-colors hover:border-rose/40 hover:text-rose"
            >
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
