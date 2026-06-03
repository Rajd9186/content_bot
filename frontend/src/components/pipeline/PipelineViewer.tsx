"use client";

import { useState } from "react";
import { BookOutput, Network } from "lucide-react";
import { usePipelineStore } from "@/store/pipeline-store";
import { ErrorBoundary } from "@/components/common";
import { PipelineGraph } from "./PipelineGraph";
import { AgentActivityPanel } from "./AgentActivityPanel";
import { AgentTransparencyPanel } from "./AgentTransparencyPanel";
import { StreamTimeline } from "./StreamTimeline";
import { OutputWorkspace } from "./OutputWorkspace";

export function PipelineViewer() {
  const currentId = usePipelineStore((s) => s.currentId);
  const content = usePipelineStore((s) => s.content);
  const loading = usePipelineStore((s) => s.loading);
  const error = usePipelineStore((s) => s.error);
  const cancel = usePipelineStore((s) => s.cancel);
  const status = usePipelineStore((s) => s.status);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"pipeline" | "content">("pipeline");

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
  const hasContent = !!(content?.final_content || content?.draft_content);

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-1">
      {viewMode === "pipeline" ? (
        <>
          <div className="rounded-xl border border-border bg-card/30 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-xs font-semibold text-foreground">Pipeline Graph</h3>
              <div className="flex items-center gap-2">
                {hasContent && (
                  <button
                    onClick={() => setViewMode("content")}
                    className="flex items-center gap-1.5 rounded-lg bg-violet-500/10 border border-violet-500/20 px-3 py-1 text-[11px] font-medium text-violet-400 hover:bg-violet-500/20 transition-colors"
                  >
                    <BookOutput className="h-3 w-3" />
                    Content View
                  </button>
                )}
                {isRunning && (
                  <button
                    onClick={() => cancel(currentId)}
                    className="rounded-lg border border-red-500/30 px-3 py-1 text-[11px] font-medium text-red-300 hover:bg-red-500/10 transition-colors"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
            <PipelineGraph onNodeClick={setSelectedNodeId} />
          </div>

          <StreamTimeline />

          <AgentActivityPanel />
        </>
      ) : (
        <>
          <div className="rounded-xl border border-border bg-card/30 p-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-foreground">Generated Content</h3>
              <button
                onClick={() => setViewMode("pipeline")}
                className="flex items-center gap-1.5 rounded-lg bg-secondary/60 border border-border px-3 py-1 text-[11px] font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                <Network className="h-3 w-3" />
                Pipeline View
              </button>
            </div>
          </div>
          <div className="flex-1 min-h-0">
            <OutputWorkspace />
          </div>
        </>
      )}

      <AgentTransparencyPanel
        nodeId={selectedNodeId}
        onClose={() => setSelectedNodeId(null)}
      />
    </div>
  );
}