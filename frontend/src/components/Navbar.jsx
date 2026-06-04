import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { LogOut, ChevronDown, User } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

const LINKS = [
  { label: "How it works", href: "#how" },
  { label: "Live demo", href: "#demo" },
  { label: "Platform", href: "#features" },
  { label: "Impact", href: "#impact" },
];

function Avatar({ user }) {
  const initial = (user.displayName || user.email || "U").charAt(0).toUpperCase();
  if (user.photoURL) {
    return <img src={user.photoURL} alt="" className="h-7 w-7 rounded-full" />;
  }
  return (
    <span className="grid h-7 w-7 place-items-center rounded-full bg-gradient-to-br from-brand to-brand-soft text-xs font-bold text-white">
      {initial}
    </span>
  );
}

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, signOutUser, openSignIn, openProfile } = useAuth();
  const menuRef = useRef(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  return (
    <>
      <motion.header
        initial={{ y: -80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.7, ease: "easeOut" }}
        className="fixed inset-x-0 top-0 z-50 flex justify-center px-4 pt-4"
      >
        <nav
          className={`flex w-full max-w-7xl items-center justify-between rounded-2xl px-4 py-3 transition-all duration-300 md:px-6 ${
            scrolled ? "glass-strong shadow-card" : "border border-transparent"
          }`}
        >
          <a href="#top" className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand to-brand-soft text-lg shadow-glow">
              👻
            </span>
            <span className="font-display text-lg font-bold tracking-tight text-white">
              Specter<span className="text-brand-soft">Ops</span>
            </span>
          </a>

          <div className="hidden items-center gap-7 md:flex">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="text-sm font-medium text-zinc-400 transition-colors hover:text-white"
              >
                {l.label}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-3">
            {user ? (
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] py-1 pl-1 pr-2.5 transition-colors hover:border-white/20"
                >
                  <Avatar user={user} />
                  <span className="hidden text-sm font-medium text-zinc-200 sm:block">
                    {user.displayName}
                  </span>
                  <ChevronDown className="h-3.5 w-3.5 text-zinc-500" />
                </button>
                {menuOpen && (
                  <div className="absolute right-0 mt-2 w-56 overflow-hidden rounded-xl border border-white/10 bg-ink-850/95 p-1.5 shadow-card backdrop-blur-xl">
                    <div className="px-3 py-2">
                      <p className="truncate text-sm font-semibold text-white">{user.displayName}</p>
                      <p className="truncate text-xs text-zinc-500">{user.email}</p>
                    </div>
                    <div className="my-1 h-px bg-white/8" />
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        openProfile();
                      }}
                      className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-zinc-300 transition-colors hover:bg-white/5 hover:text-white"
                    >
                      <User className="h-4 w-4" /> Profile
                    </button>
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        signOutUser();
                      }}
                      className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-zinc-300 transition-colors hover:bg-white/5 hover:text-white"
                    >
                      <LogOut className="h-4 w-4" /> Sign out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <button
                  onClick={openSignIn}
                  className="hidden text-sm font-medium text-zinc-300 transition-colors hover:text-white sm:block"
                >
                  Sign in
                </button>
                <button onClick={openSignIn} className="btn-primary !px-5 !py-2.5">
                  Get started
                </button>
              </>
            )}
          </div>
        </nav>
      </motion.header>
    </>
  );
}
