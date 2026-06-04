import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Mail, Lock, Loader2 } from "lucide-react";
import { useAuth } from "../../context/AuthContext.jsx";

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 48 48">
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.4 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.5 29.5 4.5 24 4.5 13.2 4.5 4.5 13.2 4.5 24S13.2 43.5 24 43.5 43.5 34.8 43.5 24c0-1.2-.1-2.3-.4-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 12 24 12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.5 29.5 4.5 24 4.5 16.3 4.5 9.7 8.9 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 43.5c5.2 0 10-2 13.6-5.2l-6.3-5.3C29.3 34.6 26.8 35.5 24 35.5c-5.3 0-9.7-3.6-11.3-8.4l-6.5 5C9.6 39 16.3 43.5 24 43.5z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4 5.5l6.3 5.3C41.6 35.3 43.5 30.1 43.5 24c0-1.2-.1-2.3.1-3.5z" />
    </svg>
  );
}

export default function SignInModal({ open, onClose }) {
  const { signInGoogle, signInEmail, mode } = useAuth();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function handleGoogle() {
    setBusy(true);
    setErr(null);
    const r = await signInGoogle();
    setBusy(false);
    if (r.ok) onClose();
    else setErr(r.error);
  }

  async function handleEmail(e) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    const r = await signInEmail(email, password, isSignUp);
    setBusy(false);
    if (r.ok) onClose();
    else setErr(r.error);
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div
            className="absolute inset-0 bg-ink-950/80 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="border-glow relative w-full max-w-md overflow-hidden rounded-2xl border border-white/10 bg-ink-900/90 p-7 shadow-card backdrop-blur-xl"
          >
            <button
              onClick={onClose}
              className="absolute right-4 top-4 grid h-8 w-8 place-items-center rounded-lg text-zinc-500 transition-colors hover:bg-white/5 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="mb-6 text-center">
              <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-xl bg-gradient-to-br from-brand to-brand-soft text-2xl shadow-glow">
                👻
              </div>
              <h3 className="font-display text-xl font-bold text-white">
                {isSignUp ? "Create your account" : "Welcome back"}
              </h3>
              <p className="mt-1 text-sm text-zinc-500">
                {isSignUp ? "Save your incident investigations." : "Sign in to your SpecterOps workspace."}
              </p>
            </div>

            <button
              onClick={handleGoogle}
              disabled={busy}
              className="flex w-full items-center justify-center gap-3 rounded-xl border border-white/15 bg-white/[0.04] px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/[0.08] disabled:opacity-60"
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <GoogleIcon />}
              Continue with Google
            </button>

            <div className="my-5 flex items-center gap-3 text-xs text-zinc-600">
              <span className="h-px flex-1 bg-white/10" /> or <span className="h-px flex-1 bg-white/10" />
            </div>

            <form onSubmit={handleEmail} className="space-y-3">
              <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3">
                <Mail className="h-4 w-4 text-zinc-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full bg-transparent py-3 text-sm text-white placeholder-zinc-600 outline-none"
                />
              </div>
              <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3">
                <Lock className="h-4 w-4 text-zinc-500" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-transparent py-3 text-sm text-white placeholder-zinc-600 outline-none"
                />
              </div>

              {err && <p className="text-xs text-rose">{err}</p>}

              <button type="submit" disabled={busy} className="btn-primary w-full">
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {isSignUp ? "Create account" : "Sign in"}
              </button>
            </form>

            <p className="mt-5 text-center text-xs text-zinc-500">
              {isSignUp ? "Already have an account?" : "New to SpecterOps?"}{" "}
              <button
                onClick={() => setIsSignUp((v) => !v)}
                className="font-semibold text-brand-soft hover:underline"
              >
                {isSignUp ? "Sign in" : "Create one"}
              </button>
            </p>

            {mode === "demo" && (
              <p className="mt-4 rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2 text-center text-[11px] text-zinc-500">
                Demo auth active — add Firebase keys to enable real Google / email sign-in.
              </p>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
