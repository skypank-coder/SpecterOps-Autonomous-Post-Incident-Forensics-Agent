import { createContext, useContext, useEffect, useRef, useState } from "react";
import SignInModal from "../components/auth/SignInModal.jsx";
import ProfileModal from "../components/auth/ProfileModal.jsx";

/**
 * Auth that is REAL when Firebase is configured and gracefully falls back to a
 * local demo identity otherwise — so the app works with zero setup, and becomes
 * production auth the moment you add VITE_FIREBASE_* env vars.
 *
 * The provider also owns the sign-in and profile modals so any component can
 * open them via `openSignIn()` / `openProfile()`.
 */
const AuthContext = createContext(null);

const FIREBASE_CONFIG = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const FIREBASE_ENABLED = Boolean(FIREBASE_CONFIG.apiKey);
const DEMO_KEY = "specterops.demoUser";

function mapUser(u) {
  if (!u) return null;
  return {
    uid: u.uid,
    email: u.email,
    displayName: u.displayName || (u.email ? u.email.split("@")[0] : "User"),
    photoURL: u.photoURL || null,
  };
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(null);
  const [signInOpen, setSignInOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const fb = useRef({ auth: null, mod: null });

  useEffect(() => {
    let unsub = () => {};
    (async () => {
      if (FIREBASE_ENABLED) {
        try {
          const { initializeApp } = await import("firebase/app");
          const mod = await import("firebase/auth");
          const app = initializeApp(FIREBASE_CONFIG);
          const auth = mod.getAuth(app);
          fb.current = { auth, mod };
          unsub = mod.onAuthStateChanged(auth, (u) => {
            setUser(mapUser(u));
            setReady(true);
          });
          return;
        } catch (e) {
          // fall through to demo mode if firebase fails to load
        }
      }
      // Demo mode
      try {
        const saved = localStorage.getItem(DEMO_KEY);
        if (saved) setUser(JSON.parse(saved));
      } catch {}
      setReady(true);
    })();
    return () => unsub();
  }, []);

  function persistDemo(u) {
    setUser(u);
    try {
      localStorage.setItem(DEMO_KEY, JSON.stringify(u));
    } catch {}
  }

  async function signInGoogle() {
    setError(null);
    if (FIREBASE_ENABLED && fb.current.auth) {
      try {
        const { GoogleAuthProvider, signInWithPopup } = fb.current.mod;
        await signInWithPopup(fb.current.auth, new GoogleAuthProvider());
        return { ok: true };
      } catch (e) {
        setError(e.message);
        return { ok: false, error: e.message };
      }
    }
    persistDemo({
      uid: "demo-google",
      email: "demo.user@gmail.com",
      displayName: "Demo User",
      photoURL: null,
      demo: true,
    });
    return { ok: true };
  }

  async function signInEmail(email, password, isSignUp = false) {
    setError(null);
    if (FIREBASE_ENABLED && fb.current.auth) {
      try {
        const { signInWithEmailAndPassword, createUserWithEmailAndPassword } = fb.current.mod;
        const fn = isSignUp ? createUserWithEmailAndPassword : signInWithEmailAndPassword;
        await fn(fb.current.auth, email, password);
        return { ok: true };
      } catch (e) {
        setError(e.message);
        return { ok: false, error: e.message };
      }
    }
    if (!email || !password) {
      const msg = "Email and password are required";
      setError(msg);
      return { ok: false, error: msg };
    }
    persistDemo({
      uid: `demo-${email}`,
      email,
      displayName: email.split("@")[0],
      photoURL: null,
      demo: true,
    });
    return { ok: true };
  }

  async function signOutUser() {
    if (FIREBASE_ENABLED && fb.current.auth) {
      try {
        await fb.current.mod.signOut(fb.current.auth);
      } catch {}
    }
    try {
      localStorage.removeItem(DEMO_KEY);
    } catch {}
    setUser(null);
  }

  const value = {
    user,
    ready,
    error,
    mode: FIREBASE_ENABLED ? "firebase" : "demo",
    signInGoogle,
    signInEmail,
    signOutUser,
    openSignIn: () => setSignInOpen(true),
    openProfile: () => setProfileOpen(true),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
      <SignInModal open={signInOpen} onClose={() => setSignInOpen(false)} />
      <ProfileModal open={profileOpen} onClose={() => setProfileOpen(false)} />
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
