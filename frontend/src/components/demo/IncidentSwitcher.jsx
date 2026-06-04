import { Plus } from "lucide-react";

const SEV_DOT = {
  CRITICAL: "bg-rose",
  HIGH: "bg-amber",
  MEDIUM: "bg-cyan",
  LOW: "bg-zinc-500",
};

const STATUS_DOT = {
  COMPLETE: "bg-mint",
  FAILED: "bg-rose",
};

export default function IncidentSwitcher({ incidents, activeId, onSelect, onNew }) {
  if (!incidents.length) return null;
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1">
      <button
        onClick={onNew}
        className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-dashed border-white/15 px-3 py-2 text-xs font-semibold text-zinc-300 transition-colors hover:border-brand/40 hover:text-white"
      >
        <Plus className="h-3.5 w-3.5" /> New
      </button>
      {incidents.map((inc) => {
        const active = inc.id === activeId;
        const dot = STATUS_DOT[inc.status] || SEV_DOT[inc.severity] || "bg-zinc-500";
        return (
          <button
            key={inc.id}
            onClick={() => onSelect(inc.id)}
            className={`inline-flex shrink-0 items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
              active
                ? "border-brand/40 bg-brand/10 text-white"
                : "border-white/10 bg-white/[0.02] text-zinc-400 hover:text-white"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${dot} ${
                !["COMPLETE", "FAILED"].includes(inc.status) ? "animate-pulse" : ""
              }`}
            />
            <span className="max-w-[180px] truncate">{inc.title}</span>
          </button>
        );
      })}
    </div>
  );
}
