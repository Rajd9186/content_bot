"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { StreamTimeline } from "./StreamTimeline";
import { usePipelineStore } from "@/store/pipeline-store";
import { ErrorBoundary } from "@/components/common";
import { PipelineGraph } from "./PipelineGraph";
import { AgentActivityPanel } from "./AgentActivityPanel";
import { AgentTransparencyPanel } from "./AgentTransparencyPanel";

export function PipelineViewer() {
  const currentId = usePipelineStore((s) => s.currentId);
  const content = usePipelineStore((s) => s.content);
  const timeline = usePipelineStore((s) => s.timeline);
  const loading = usePipelineStore((s) => s.loading);
  const error = usePipelineStore((s) => s.error);
  const cancel = usePipelineStore((s) => s.cancel);
  const status = usePipelineStore((s) => s.status);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  if (!currentId) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">Select a pipeline to view details</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-400" />
      </div>
    );
  }

  if (error) return <ErrorBoundary error={error} />;

  const isRunning = status?.status === "running";
  const entries = timeline?.timeline ?? [];
  const stripFences = (s: string) => s.replace(/^```markdown\s*/gm, "").replace(/^```\s*$/gm, "").trim();
  const finalContent = content?.final_content ? stripFences(content.final_content) : null;
  const draftContent = content?.draft_content ? stripFences(content.draft_content) : null;

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-1">
      <div className="rounded-xl border border-border bg-card/30 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-foreground">Pipeline Graph</h3>
          {isRunning && (
            <button
              onClick={() => cancel(currentId)}
              className="rounded-lg border border-red-500/30 px-3 py-1 text-[11px] font-medium text-red-300 hover:bg-red-500/10 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
        <PipelineGraph onNodeClick={setSelectedNodeId} />
      </div>

      <StreamTimeline />

      <AgentActivityPanel />

      {(finalContent || draftContent) && (
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <h3 className="mb-3 text-xs font-semibold text-foreground">Generated Content</h3>
          <div className="prose prose-invert max-w-none text-xs text-muted-foreground">
            <pre className="whitespace-pre-wrap rounded-lg bg-black/30 p-3 text-[11px] leading-relaxed">
              {finalContent ?? draftContent ?? ""}
            </pre>
          </div>
        </div>
      )}

      <AgentTransparencyPanel
        nodeId={selectedNodeId}
        onClose={() => setSelectedNodeId(null)}
      />
    </div>
  );
}