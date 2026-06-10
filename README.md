<!--
  NOTE FOR MAINTAINER: update the CI badge URL below to your real GitHub
  owner/repo if it differs from "skypank-coder/SpecterOps-Autonomous-Post-Incident-Forensics-Agent".
-->

<div align="center">

# 👻 SpecterOps

### Autonomous Post-Incident Forensics Agent

**When your production dies at 3am, SpecterOps wakes up instead of you.**

A four-agent autonomous SRE that turns a raw Dynatrace alert into a complete,
evidence-backed post-mortem in **under 60 seconds** — no human in the loop.



[![Live Demo](https://img.shields.io/badge/▶_Live_Demo-specterops--848e3.web.app-00f5a0?style=for-the-badge)](https://specterops-848e3.web.app)
[![Watch the Demo](https://img.shields.io/badge/▶_Watch_Demo-YouTube-ff0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/dWa-vSn7WMo)

[![CI](https://github.com/skypank-coder/SpecterOps-Autonomous-Post-Incident-Forensics-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/skypank-coder/SpecterOps-Autonomous-Post-Incident-Forensics-Agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-00f5a0.svg)](LICENSE)
[![Partner: Dynatrace](https://img.shields.io/badge/Partner-Dynatrace-9b6cff)]()
[![AI: Gemini 2.5 Flash](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-4f8cff)]()
[![Frontend: Firebase](https://img.shields.io/badge/Frontend-Firebase%20Hosting-f5a623)]()
[![Backend: Cloud Run](https://img.shields.io/badge/Backend-Cloud%20Run-4f8cff)]()
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776ab.svg)]()
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)]()

<br/>

*Built for the Google Cloud Rapid Agent Hackathon 2026 — Dynatrace Partner Track.*

[Quick Start](#-quick-start) · [How It Works](#-how-it-works) · [The Demo](#-the-demo) · [Architecture](#-architecture) · [Testing](#-testing--ci)

</div>

---

## ⚡ The 60-second story

> It's 3am. A checkout flow is throwing `503`s. Dynatrace fires an alert. Normally a
> human gets paged, rubs their eyes, and spends an hour pivoting between traces, logs,
> metrics and dashboards to find out *why*.

**SpecterOps does it autonomously, while you sleep.** It receives the alert, investigates
the live telemetry, reasons about cause and effect, and hands you a finished post-mortem —
root cause, causal chain, blast radius, and a one-line fix — before you've finished reading
the page notification.

In the reference scenario it traces a **34% error-rate outage** back to a single
**missing database index** on `payment_methods.user_id` — through a circuit-breaker
cascade across three services — with **94% confidence, in ~0.3s of compute.**

---

## ✨ What's inside

- 🤖 **Four autonomous agents** orchestrated end-to-end, reasoning with **Google Gemini 2.5 Flash**.
- 🟣 **Official Dynatrace MCP server integration** — the agent is a Model Context Protocol client that calls real MCP tools (`list_problems`, `execute_dql`, `find_entity_by_name`) to **browse all open problems** and investigate any one with live telemetry.
- 🧪 **Scenario library + custom incidents** — four real-world failure scenarios (missing index, memory leak, bad deploy, dependency outage) plus a **"describe your own"** form.
- 📡 **Real-time SSE streaming** — every agent's start/finish streams live to the dashboard.
- 🕸️ **D3 causal graph** + **Three.js** 3D hero + **Framer Motion** — a business-grade UI, not a toy.
- 🔐 **Firebase auth** (Google + email) with a graceful demo fallback; investigations are saved **per user**.
- 💾 **Cloud Firestore persistence** — history survives restarts on Google Cloud; graceful in-memory fallback when unset.
- 📤 **Export & deliver** — copy/download the post-mortem as Markdown, or **send it to Slack**.
- 🛡️ **Resilient by design** — a Gemini model-fallback chain, a scenario-accurate offline mode, and graceful degradation everywhere mean it runs with **zero accounts** and never breaks on stage.
- ✅ **Tested** — `pytest` suite + **GitHub Actions CI** on every push.

> Every integration is optional and upgrades a capability from *demo* → *real*. See
> **[INTEGRATIONS.md](INTEGRATIONS.md)** for exact setup (Gemini, Dynatrace, Firestore, Firebase, Slack).

---

## 🧠 How it works

SpecterOps is a pipeline of four specialized agents. Each one does a single job well and
hands structured state to the next. Every step streams to the dashboard live over SSE.

```
     Dynatrace problem  (live pull · webhook · scenario · custom incident)
                                   │
                                   ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  🛡️  SentinelAgent        Classify the alert · extract entities,   │
   │                           severity, category & metrics to pull     │
   ├──────────────────────────────────────────────────────────────────┤
   │  🔍  TraceArchaeologist   Query Dynatrace in parallel —            │
   │                           problems · metrics · entities · logs     │
   │                           → reconstruct a chronological timeline    │
   ├──────────────────────────────────────────────────────────────────┤
   │  🎯  BlameMapper          Build a causal graph · isolate the root  │
   │                           cause with a confidence score            │
   ├──────────────────────────────────────────────────────────────────┤
   │  📝  NarratorAgent        Author a full Markdown post-mortem        │
   │      (Gemini 2.5 Flash)   (impact · timeline · remediation)         │
   └──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
     Real-time SSE dashboard  ·  D3 causal graph  ·  rendered post-mortem
```

| # | Agent | Responsibility | Output |
|:-:|:------|:---------------|:-------|
| 1 | 🛡️ **SentinelAgent** | Classifies the alert, extracts the primary service, severity, category and the metrics worth investigating | Classification + investigation plan |
| 2 | 🔍 **TraceArchaeologist** | Pulls traces, logs, metrics and topology from Dynatrace **in parallel**, compresses them, and reconstructs the incident timeline | Timeline + headline impact metrics |
| 3 | 🎯 **BlameMapper** | Reasons over the timeline to build a directed causal graph and pin the single root cause | Causal graph + confidence score |
| 4 | 📝 **NarratorAgent** | Writes a production-grade post-mortem in Markdown using all gathered evidence | 10-section post-mortem |

---

## 🎬 The demo

> 📺 **[Watch the 3-minute demo on YouTube →](https://youtu.be/dWa-vSn7WMo)**

> Sign in, then **choose what to investigate** — a **live open problem pulled straight from
> your Dynatrace tenant**, a built-in failure scenario, or your own typed incident — and watch
> all four agents diagnose it live in ~30–60 seconds.

**Example — the "missing index" scenario:**

1. 🛡️ SentinelAgent classifies it as a `DATABASE_ISSUE` on `payment-service`.
2. 🔍 TraceArchaeologist reconstructs a 7-event timeline and surfaces the impact strip:
   **33.9% error rate · 4.2s p99 (35× baseline) · 50 traces analyzed**.
3. 🎯 BlameMapper draws the D3 causal graph and pins the root cause at **94% confidence**.
4. 📝 NarratorAgent writes the post-mortem — including the one-line fix:
   ```sql
   CREATE INDEX CONCURRENTLY idx_payment_methods_user_id ON payment_methods (user_id);
   ```
5. 🟣 One click **pushes the finished RCA back onto the Dynatrace problem** as a comment.

A live **"Time to Diagnose"** counter proves the speed claim on screen.

> 💡 **Runs with zero accounts:** `DEMO_MODE=true` uses realistic simulated telemetry, and
> without a `GEMINI_API_KEY` each agent uses a scenario-accurate offline response — so the
> full pipeline always completes. **Add a Gemini key + a Dynatrace token to make it fully
> real:** live problems, real LLM reasoning, RCA pushed back to Dynatrace.

---

## 🚀 Quick start

```bash
# 1 — Backend deps
cd backend
python -m venv venv && source venv/bin/activate     # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# 2 — Configure (DEMO_MODE=true needs no accounts; add a Gemini key for live LLM output)
cp ../.env.example .env

# 3 — Run the backend  → http://localhost:8000
uvicorn main:app --reload --port 8000

# 4 — Frontend (new terminal)  → http://localhost:5173
cd frontend && npm install && npm run dev

# 5 — Open the dashboard, sign in, and pick a scenario (or a live Dynatrace problem)
```

> For **live Gemini reasoning**, drop a key from [Google AI Studio](https://aistudio.google.com/apikey)
> into `backend/.env` as `GEMINI_API_KEY`. A model-fallback chain keeps the
> demo working even if a specific model id has been retired.

---

## 🏗️ Architecture

<div align="center">

| Layer | Technology |
|:------|:-----------|
| **Agents / Backend** | Python 3.11 · FastAPI · asyncio · Server-Sent Events |
| **Reasoning** | Google **Gemini 2.5 Flash** on **Vertex AI** (Google Cloud), via the `google-genai` SDK |
| **Observability** | **Dynatrace** — official **MCP server** (`list_problems` · `execute_dql` · `find_entity_by_name`) locally; **REST API** headless on Cloud Run |
| **Frontend** | React 18 + Vite · Tailwind CSS · Framer Motion · **Three.js** (3D hero) · **D3** force-directed graph |
| **Auth** | Firebase Authentication (Google + email) with graceful demo fallback |
| **Persistence** | **Google Cloud Firestore** · graceful in-memory fallback |
| **Deployment** | Docker · **Google Cloud Run** (backend) · **Firebase Hosting** (frontend) |
| **Quality** | `pytest` + `pytest-asyncio` · GitHub Actions CI |

</div>

### Dynatrace integration — via the official MCP server

This is the heart of the Dynatrace track. The `TraceArchaeologist` agent is a **Model
Context Protocol client** ([`dynatrace_mcp.py`](backend/connectors/dynatrace_mcp.py)) that
connects to the **official Dynatrace MCP server** (`@dynatrace-oss/dynatrace-mcp-server`)
and calls real MCP tools to investigate live incidents:

| MCP tool | What SpecterOps does with it |
|:---|:---|
| **`list_problems`** | Pull live open problems from the tenant (the picker + the chosen incident) |
| **`execute_dql`** | Fetch logs / events / spans / metrics via Grail DQL as investigation evidence |
| **`find_entity_by_name`** | Resolve the affected monitored entity |

A single MCP server process + session is spawned and reused, so the interactive Dynatrace
OAuth login happens **once** per run.

**Two live paths, by design — read this if you're judging:**

| Where it runs | Live Dynatrace path | Why |
|:---|:---|:---|
| **Locally** (your machine / the demo video) | **Official MCP server** — `list_problems`, `execute_dql`, `find_entity_by_name` fire against the tenant | The MCP server authenticates through an **interactive browser OAuth** login (Dynatrace SSO) |
| **Hosted** (Cloud Run, the judging URL) | **Dynatrace REST API** against the same tenant | Cloud Run is **headless** — it can't open a browser for the MCP OAuth flow, so the deployed service uses Dynatrace's token-based REST API for always-on, never-expiring operation |

Both talk to real Dynatrace data; the agent code is identical and simply selects the path at
startup. The MCP integration is shown live in the demo video and lives in
[`dynatrace_mcp.py`](backend/connectors/dynatrace_mcp.py); the hosted URL proves the same agent
running as a real Google Cloud product.

`DEMO_MODE=true` uses a deterministic simulation ([`scenarios.py`](backend/connectors/scenarios.py))
so the system also runs with **zero accounts**. Live values are unit-normalized; anything that
can't be resolved is hidden rather than shown wrong.

### Environment variables & going live

Everything runs with no keys. Each one upgrades a capability from demo → real — see the full
step-by-step **[INTEGRATIONS.md](INTEGRATIONS.md)** (Gemini, Dynatrace, Firestore, Firebase, Slack).

| Variable | Unlocks |
|:---|:---|
| `GOOGLE_GENAI_USE_VERTEXAI=true` + `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` | Gemini reasoning on **Vertex AI** (Google Cloud) |
| `DEMO_MODE=false` + `DYNATRACE_URL` + `DYNATRACE_API_TOKEN` | Investigate real Dynatrace problems |
| `GOOGLE_CLOUD_PROJECT` (+ Firestore enabled) | Persistent incident history on **Cloud Firestore** |
| `VITE_FIREBASE_*` (in `frontend/.env`) | Real Google / email sign-in |
| `SLACK_WEBHOOK_URL` | Deliver post-mortems to Slack |

---

## ✅ Testing & CI

[![CI](https://github.com/skypank-coder/SpecterOps-Autonomous-Post-Incident-Forensics-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/skypank-coder/SpecterOps-Autonomous-Post-Incident-Forensics-Agent/actions/workflows/ci.yml)

GitHub Actions runs on every push and PR:

- **Backend** — the full `pytest` suite on Python **3.11 and 3.12**.
- **Frontend** — a production `vite build`.

The suite ([`tests/test_pipeline.py`](backend/tests/test_pipeline.py)) covers the
end-to-end pipeline, impact/timing population, timeline ordering, post-mortem structure,
the Dynatrace client in demo mode, and the integrity of the simulated incident data.

```bash
cd backend
DEMO_MODE=true python -m pytest      # 7 passed
```

---

## 📂 Project structure

```
SpecterOps/
├── .github/workflows/ci.yml    # backend tests + frontend build
├── firebase.json · .firebaserc # Firebase Hosting (frontend deploy)
├── backend/Dockerfile          # container → Google Cloud Run (Node + Python + MCP)
├── INTEGRATIONS.md             # go-live guide (Gemini · Dynatrace · Firestore · Firebase · Slack)
├── LICENSE                     # MIT
├── backend/                    # FastAPI app
│   ├── agents/                 # orchestrator + the 4 agents
│   ├── connectors/             # Dynatrace MCP client + scenario engine
│   ├── models/                 # Pydantic domain models
│   ├── routes/                 # incidents · webhook · SSE stream · config
│   ├── utils/                  # Gemini client (model fallback chain)
│   ├── storage.py              # Cloud Firestore persistence (graceful fallback)
│   └── tests/                  # pytest suite
└── frontend/                   # React + Vite dashboard
    └── src/components/         # launcher · agents · D3 graph · evidence · post-mortem · auth
```

---

## 🏆 How it maps to the judging criteria

| Criterion               | How SpecterOps delivers                                                                 |
|:------------------------|:----------------------------------------------------------------------------------------|
| **Autonomy**            | Four agents run a full alert → post-mortem pipeline with **no human in the loop**.       |
| **Use of Gemini**       | Gemini 2.5 Flash drives classification, timeline reconstruction, causal reasoning & authoring. |
| **Partner (Dynatrace)** | Pulls **real** open problems (problems · metrics · entities · logs) and **pushes the RCA back** onto the problem. |
| **Technical execution** | Async parallel data gathering, live SSE streaming, D3 visualization, graceful fallbacks, CI + tests. |
| **Impact / wow**        | A real outage diagnosed end-to-end in under 60 seconds — **live on screen**.             |
| **Polish**              | Dark-terminal dashboard, real-time agent timeline, headline impact metrics, rendered post-mortem. |

---

## 🗺️ Roadmap

Already shipped: live Dynatrace problem pull + RCA push-back, scenario library + custom
incidents, Cloud Firestore persistence, Firebase auth, Slack delivery. Next:

- 🤖 Approval-gated **auto-remediation execution** (wire the proposed fix into CI/CD)
- 👥 **Per-user Dynatrace** connect (multi-tenant, OAuth) so each user investigates their own tenant
- 🎫 Auto-file a **GitHub / Jira** remediation ticket from the post-mortem
- 🔗 **Multi-incident correlation** — detect when several problems share one root cause
- 🧩 Native **Dynatrace App** (run SpecterOps inside the Dynatrace platform)

---

## 📜 License

[MIT](LICENSE) © 2026 SpecterOps Contributors

<div align="center">
<br/>
<sub>Built with Gemini 2.5 Flash on Vertex AI · Dynatrace MCP · Cloud Run · Firebase — for the Google Cloud Rapid Agent Hackathon 2026.</sub>
</div>
