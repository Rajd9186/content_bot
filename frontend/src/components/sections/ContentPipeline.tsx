"use client";

import dynamic from "next/dynamic";

const PipelineForm = dynamic(() => import("@/components/pipeline/PipelineForm").then((m) => ({ default: m.PipelineForm })), { ssr: false });
const PipelineViewer = dynamic(() => import("@/components/pipeline/PipelineViewer").then((m) => ({ default: m.PipelineViewer })), { ssr: false });
const PipelineList = dynamic(() => import("@/components/pipeline/PipelineList").then((m) => ({ default: m.PipelineList })), { ssr: false });

export function ContentPipeline() {
  return (
    <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-[300px_1fr] xl:grid-cols-[300px_1fr_220px]">
      <div className="space-y-4 overflow-y-auto">
        <PipelineForm />
        <div className="hidden lg:block">
          <PipelineList />
        </div>
      </div>
      <div className="min-h-0 overflow-y-auto">
        <PipelineViewer />
      </div>
      <div className="hidden xl:block space-y-4">
        <div className="rounded-2xl border border-border bg-card/40 p-4 backdrop-blur-xl">
          <h3 className="mb-3 text-xs font-semibold text-foreground uppercase tracking-wide">Quick Info</h3>
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            Select or create a pipeline to generate AI content. Each pipeline runs through 8 stages of automated content creation with real-time streaming.
          </p>
        </div>
      </div>
    </div>
  );
}