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
  const dt = config.dynatrace?.connected;
  const store = config.storage?.connected;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge
        icon={Cpu}
        label={gemini ? `Gemini · ${config.gemini.model || "live"}` : "Gemini · offline"}
        on={gemini}
        onText="Live Gemini reasoning"
        offText="Offline fallback (add GEMINI_API_KEY)"
      />
      <Badge
        icon={Activity}
        label={dt ? "Dynatrace · live" : "Dynatrace · demo"}
        on={dt}
        onText="Connected to live Dynatrace"
        offText="Simulated telemetry (DEMO_MODE)"
      />
      <Badge
        icon={Database}
        label={store ? "DB · persisted" : "DB · in-memory"}
        on={store}
        onText="Incidents persisted to MongoDB"
        offText="In-memory (add MONGODB_URI)"
      />
    </div>
  );
}
