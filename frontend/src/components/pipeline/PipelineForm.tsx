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
    <div className="rounded-2xl border border-border bg-card/60 p-5 backdrop-blur-xl shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-foreground flex items-center gap-2">
        <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse-soft" />
        Create Pipeline
      </h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="mb-1.5 block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">Topic</label>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter content topic..."
            className="input-glow w-full rounded-xl border border-border bg-secondary/30 px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:border-violet-500/50 focus:outline-none transition-all"
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="mb-1.5 block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">Audience</label>
            <select
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              className="w-full rounded-xl border border-border bg-secondary/30 px-2 py-2.5 text-xs text-foreground focus:border-violet-500/50 focus:outline-none transition-all cursor-pointer"
            >
              {AUDIENCE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">Tone</label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full rounded-xl border border-border bg-secondary/30 px-2 py-2.5 text-xs text-foreground focus:border-violet-500/50 focus:outline-none transition-all cursor-pointer"
            >
              {TONE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full rounded-xl border border-border bg-secondary/30 px-2 py-2.5 text-xs text-foreground focus:border-violet-500/50 focus:outline-none transition-all cursor-pointer"
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
          className="btn-press w-full rounded-xl bg-gradient-to-r from-violet-600 to-violet-700 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-violet-600 hover:shadow-violet-500/30 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200"
        >
          {loading ? "Starting..." : "Start Pipeline"}
        </button>
      </form>
    </div>
  );
}