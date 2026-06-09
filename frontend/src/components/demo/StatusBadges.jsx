import { Cpu, Database, Activity } from "lucide-react";

function Badge({ icon: Icon, label, on, onText, offText }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold ${
        on
          ? "border-mint/30 bg-mint/10 text-mint"
          : "border-white/10 bg-white/[0.03] text-zinc-500"
      }`}
      title={on ? onText : offText}
    >
      <Icon className="h-3 w-3" />
      <span className="hidden sm:inline">{label}</span>
      <span className={`h-1.5 w-1.5 rounded-full ${on ? "bg-mint" : "bg-zinc-600"}`} />
    </span>
  );
}

export default function StatusBadges({ config }) {
  if (!config) return null;
  const gemini = config.gemini?.connected;
  const geminiVia = config.gemini?.provider; // "vertex" | "aistudio"
  const dt = config.dynatrace?.connected;
  const dtVia = config.dynatrace?.via; // "mcp" | "rest" | null
  const store = config.storage?.connected;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge
        icon={Cpu}
        label={gemini ? (geminiVia === "vertex" ? "Gemini · Vertex AI" : `Gemini · ${config.gemini.model || "live"}`) : "Gemini · offline"}
        on={gemini}
        onText={geminiVia === "vertex" ? "Gemini 2.5 Flash on Vertex AI (Google Cloud)" : "Live Gemini reasoning"}
        offText="Offline fallback (add GEMINI_API_KEY)"
      />
      <Badge
        icon={Activity}
        label={dt ? (dtVia === "mcp" ? "Dynatrace · MCP" : "Dynatrace · live") : "Dynatrace · demo"}
        on={dt}
        onText={dtVia === "mcp" ? "Live via the official Dynatrace MCP server" : "Connected to live Dynatrace"}
        offText="Simulated telemetry (DEMO_MODE)"
      />
      <Badge
        icon={Database}
        label={store ? "Firestore · persisted" : "DB · in-memory"}
        on={store}
        onText="Incidents persisted to Cloud Firestore"
        offText="In-memory (enable Firestore)"
      />
    </div>
  );
}
