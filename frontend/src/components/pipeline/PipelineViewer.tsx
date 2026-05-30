"use client";

import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";
import { ErrorBoundary } from "@/components/common";
import { NodeStatusCard } from "./NodeStatusCard";

export function PipelineViewer() {
  const currentId = usePipelineStore((s) => s.currentId);
  const content = usePipelineStore((s) => s.content);
  const timeline = usePipelineStore((s) => s.timeline);
  const loading = usePipelineStore((s) => s.loading);
  const error = usePipelineStore((s) => s.error);
  const cancel = usePipelineStore((s) => s.cancel);
  const status = usePipelineStore((s) => s.status);

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
          <h3 className="text-xs font-semibold text-foreground">Pipeline DAG</h3>
          {isRunning && (
            <button
              onClick={() => cancel(currentId)}
              className="rounded-lg border border-red-500/30 px-3 py-1 text-[11px] font-medium text-red-300 hover:bg-red-500/10 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
        <NodeStatusCard />
      </div>

      {entries.length > 0 && (
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <h3 className="mb-3 text-xs font-semibold text-foreground">Timeline</h3>
          <div className="space-y-2">
            {entries.map((t, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      "h-2 w-2 rounded-full",
                      t.status === "completed" ? "bg-emerald-400" :
                      t.status === "running" ? "bg-blue-400 animate-pulse-soft" :
                      t.status === "failed" ? "bg-red-400" :
                      "bg-slate-500",
                    )}
                  />
                  {i < entries.length - 1 && <div className="mt-0.5 h-4 w-px bg-border" />}
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-foreground">{t.node}</p>
                  <p className="text-[10px] text-muted-foreground">{t.status}{t.error ? ` — ${t.error}` : ""}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
    </div>
  );
}
