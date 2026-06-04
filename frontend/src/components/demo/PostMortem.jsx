import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, Download, Send, Upload } from "lucide-react";
import { API_BASE } from "../../lib/api.js";

export default function PostMortem({ incident, slackConnected, dynatraceConnected }) {
  const [copied, setCopied] = useState(false);
  const [slackState, setSlackState] = useState("idle"); // idle | sending | sent | error
  const [dtState, setDtState] = useState("idle");
  const md = incident?.postmortem;

  function copy() {
    if (!md) return;
    navigator.clipboard.writeText(md).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function download() {
    if (!md) return;
    const slug = (incident.title || "postmortem")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "")
      .slice(0, 60);
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `postmortem-${slug}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function sendSlack() {
    setSlackState("sending");
    try {
      const res = await fetch(`${API_BASE}/api/incidents/${incident.id}/share/slack`, {
        method: "POST",
      });
      setSlackState(res.ok ? "sent" : "error");
    } catch {
      setSlackState("error");
    }
    setTimeout(() => setSlackState("idle"), 2500);
  }

  async function pushToDynatrace() {
    setDtState("sending");
    try {
      const res = await fetch(`${API_BASE}/api/incidents/${incident.id}/dynatrace/comment`, {
        method: "POST",
      });
      setDtState(res.ok ? "sent" : "error");
    } catch {
      setDtState("error");
    }
    setTimeout(() => setDtState("idle"), 3000);
  }

  if (!md) {
    return (
      <div className="grid h-[420px] place-items-center text-center text-sm text-zinc-500">
        The post-mortem appears once NarratorAgent finishes writing it.
      </div>
    );
  }

  const btn =
    "inline-flex items-center gap-1.5 rounded-lg border border-white/15 px-3 py-1.5 text-xs font-semibold text-zinc-300 transition-colors";

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3">
        <div className="text-[10px] uppercase tracking-widest text-zinc-500">
          {md.length.toLocaleString()} chars · authored by Gemini 2.5
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={copy} className={`${btn} hover:border-mint/50 hover:text-mint`}>
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? "Copied" : "Copy"}
          </button>
          <button onClick={download} className={`${btn} hover:border-brand/50 hover:text-brand-soft`}>
            <Download className="h-3.5 w-3.5" /> Download .md
          </button>
          {slackConnected && (
            <button
              onClick={sendSlack}
              disabled={slackState === "sending"}
              className={`${btn} hover:border-cyan/50 hover:text-cyan`}
            >
              <Send className="h-3.5 w-3.5" />
              {slackState === "sent"
                ? "Sent ✓"
                : slackState === "error"
                ? "Failed"
                : slackState === "sending"
                ? "Sending…"
                : "Send to Slack"}
            </button>
          )}
          {dynatraceConnected && incident.dynatrace_problem_id && (
            <button
              onClick={pushToDynatrace}
              disabled={dtState === "sending"}
              className={`${btn} hover:border-brand/50 hover:text-brand-soft`}
              title="Post this root-cause analysis back onto the Dynatrace problem"
            >
              <Upload className="h-3.5 w-3.5" />
              {dtState === "sent"
                ? "Posted ✓"
                : dtState === "error"
                ? "Needs write scope"
                : dtState === "sending"
                ? "Posting…"
                : "Push to Dynatrace"}
            </button>
          )}
        </div>
      </div>
      <div className="prose-pm max-h-[520px] max-w-none overflow-y-auto pr-2">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
      </div>
    </div>
  );
}
