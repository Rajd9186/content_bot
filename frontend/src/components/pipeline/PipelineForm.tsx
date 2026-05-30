"use client";

import { useState } from "react";
import { usePipelineStore } from "@/store/pipeline-store";
import { AUDIENCE_OPTIONS, TONE_OPTIONS, PROVIDER_LABELS } from "@/lib/constants";

export function PipelineForm() {
  const create = usePipelineStore((s) => s.create);
  const run = usePipelineStore((s) => s.run);
  const loading = usePipelineStore((s) => s.loading);
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("general");
  const [tone, setTone] = useState("professional");
  const [provider, setProvider] = useState("openai");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    const id = await create(topic.trim(), audience, tone);
    setTopic("");
    if (id) run(id);
  };

  return (
    <div className="rounded-xl border border-border bg-card/40 p-5">
      <h3 className="mb-4 text-sm font-semibold text-foreground">Create Pipeline</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="mb-1 block text-[11px] font-medium text-muted-foreground">Topic</label>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter content topic..."
            className="w-full rounded-lg border border-border bg-black/20 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/40 focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/20 transition-colors"
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="mb-1 block text-[11px] font-medium text-muted-foreground">Audience</label>
            <select
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              className="w-full rounded-lg border border-border bg-black/20 px-2 py-2 text-xs text-foreground focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/20"
            >
              {AUDIENCE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-medium text-muted-foreground">Tone</label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full rounded-lg border border-border bg-black/20 px-2 py-2 text-xs text-foreground focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/20"
            >
              {TONE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-medium text-muted-foreground">Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full rounded-lg border border-border bg-black/20 px-2 py-2 text-xs text-foreground focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/20"
            >
              {Object.entries(PROVIDER_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !topic.trim()}
          className="w-full rounded-lg bg-emerald-500 py-2 text-sm font-medium text-white shadow-lg shadow-emerald-500/20 hover:bg-emerald-600 hover:shadow-emerald-500/40 disabled:cursor-not-allowed disabled:opacity-50 transition-all"
        >
          {loading ? "Starting..." : "Start Pipeline"}
        </button>
      </form>
    </div>
  );
}
