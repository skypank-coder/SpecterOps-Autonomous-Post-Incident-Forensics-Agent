# SpecterOps — Integrations & Going Live

SpecterOps runs with **zero setup** (simulated telemetry + offline reasoning). Each
integration below upgrades a part of the system from "demo" to "real". Add them in
any order — everything degrades gracefully if a key is missing.

> After editing **`backend/.env`** restart the backend. After editing
> **`frontend/.env`** restart the frontend (Vite only reads `VITE_*` at startup).

---

## 1. Gemini (AI reasoning) — free

Turns the agents from scripted offline output into **real LLM reasoning**.

1. Get a free key at **https://aistudio.google.com/apikey**.
2. In `backend/.env`:
   ```
   GEMINI_API_KEY=AIza...            # your key
   GEMINI_MODEL=gemini-2.5-flash     # recommended; blank = auto fallback chain
   ```
**Which model:** use **`gemini-2.5-flash`** — fast (keeps the live demo snappy), generous
free tier. `gemini-2.5-pro` writes slightly richer post-mortems but is slower and has
tighter free limits. If a model is unavailable the app auto-falls back down the chain.

---

## 2. Dynatrace (real incidents) — free trial

Lets SpecterOps pull **real open problems** from your tenant and analyze them.

1. Start a free **Dynatrace trial** (SaaS) — or use the public **Playground**.
2. Find your environment URL. Whatever you log in at (e.g. `https://abc12345.apps.dynatrace.com`),
   the **API host** is the `.live.` form:
   ```
   DYNATRACE_URL=https://abc12345.live.dynatrace.com
   ```
   (No trailing slash, no `/api`. The Playground's value is `https://playground.live.dynatrace.com`.)
3. Create an **Access token**: Settings → Access tokens → Generate. Tick these scopes:

   | Scope (UI) | Internal | Used for | Priority |
   |---|---|---|---|
   | Read problems | `problems.read` | `GET /api/v2/problems` — auto-pull the incident | ⭐ required |
   | Read metrics | `metrics.read` | `GET /api/v2/metrics/query` — error rate & latency | ⭐ required |
   | Read entities | `entities.read` | `GET /api/v2/entities` — topology | recommended |
   | Read logs | `logs.read` | `GET /api/v2/logs/search` — log evidence (needs Log Management) | optional |
   | Write problem comments | `problems.write` | post the RCA **back** onto the problem | optional |
4. In `backend/.env`:
   ```
   DEMO_MODE=false
   DYNATRACE_URL=https://<env-id>.live.dynatrace.com
   DYNATRACE_API_TOKEN=dt0c01....
   ```
5. Restart the backend → the **"Investigate latest live Dynatrace problem"** button appears.

**Notes & honest limits**
- Dynatrace has **no public "read traces" REST endpoint** (traces live in Grail/DQL), so
  the live path uses problems + metrics + entities + logs. Investigations still complete.
- `response.time` is returned in **microseconds** and `errors.total.rate` as a **percent** —
  SpecterOps normalizes both. If a value can't be resolved, the metric tile is hidden rather
  than shown wrong.
- **Push to Dynatrace** (posting the RCA as a problem comment) needs `problems.write`. The
  read-only Playground token returns 403 — that's expected.
- The richest visuals come from `DEMO_MODE=true` (full simulated scenarios) reasoned over by
  real Gemini. `DEMO_MODE=false` shows *real* problems, whose richness depends on your tenant.

---

## 3. MongoDB Atlas (persistent history) — free M0

Without it, incidents live in memory and reset on restart. With it, history persists.

1. Create a free account at **https://www.mongodb.com/atlas** and a free **M0** cluster.
2. **Database Access** → Add a database user (username + password).
3. **Network Access** → Add IP → allow your IP (or `0.0.0.0/0` for testing).
4. **Connect → Drivers → Python** → copy the SRV connection string and insert your password:
   ```
   MONGODB_URI=mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/specterops
   ```
5. Put it in `backend/.env`, restart. The status badge flips to **DB · persisted**.

---

## 4. Firebase Auth (real Google / email sign-in) — free

> **Why does clicking sign-in jump straight to a "demo" user?** Because Firebase isn't
> configured yet, the app uses a built-in **demo identity** so the flow works with zero setup.
> Add the keys below to get **real Google + email/password** login.

1. Create a project at **https://console.firebase.google.com**.
2. **Build → Authentication → Get started** → enable **Google** and **Email/Password**.
3. **Project settings → General → Your apps →** add a **Web app** → copy the SDK config.
4. **Authentication → Settings → Authorized domains** → add `localhost` (and your deployed domain).
5. Create **`frontend/.env`** (copy from `frontend/.env.example`) and fill:
   ```
   VITE_FIREBASE_API_KEY=...
   VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your-project
   VITE_FIREBASE_APP_ID=1:...:web:...
   ```
6. Restart the frontend (`npm run dev`). Sign-in now uses real Google/email; the modal's
   "Demo auth active" note disappears.

Signed-in users' investigations are tagged to their account and shown in their **Profile**.

---

## 5. Slack delivery (optional) — free

1. Create an **Incoming Webhook** at https://api.slack.com/messaging/webhooks.
2. In `backend/.env`: `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`
3. Restart. A **Send to Slack** button appears on the post-mortem.

---

## About auto-remediation

SpecterOps generates the **exact fix** and can **push the RCA back onto the Dynatrace
problem** as a comment (with `problems.write`). It deliberately does **not** auto-execute
fixes (creating indexes, rolling back deploys, restarting pods) — that requires direct,
privileged access to your infrastructure/CI and must stay behind a human approval gate.
Auto-applying production changes from an AALU loop is unsafe; the responsible pattern is
**diagnose autonomously → recommend the fix → human approves → automation applies it.**
That approval-gated execution is the natural next step and can be wired to your CI/CD.

---

## Per-user Dynatrace (future)

Today SpecterOps connects to **one** Dynatrace tenant configured in `backend/.env`. Letting
each signed-in user connect *their own* tenant (e.g. via OAuth + stored per-user tokens) is a
multi-tenant feature — straightforward to add on top of the current auth, but out of scope for
the single-tenant demo.
