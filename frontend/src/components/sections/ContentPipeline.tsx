"use client";

import dynamic from "next/dynamic";

const PipelineForm = dynamic(() => import("@/components/pipeline/PipelineForm").then((m) => ({ default: m.PipelineForm })), { ssr: false });
const PipelineViewer = dynamic(() => import("@/components/pipeline/PipelineViewer").then((m) => ({ default: m.PipelineViewer })), { ssr: false });
const PipelineList = dynamic(() => import("@/components/pipeline/PipelineList").then((m) => ({ default: m.PipelineList })), { ssr: false });

export function ContentPipeline() {
  return (
    <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-[320px_1fr] xl:grid-cols-[320px_1fr_240px]">
      <div className="space-y-4 overflow-y-auto">
        <PipelineForm />
        <PipelineList />
      </div>
      <div className="min-h-0 overflow-y-auto">
        <PipelineViewer />
      </div>
      <div className="hidden xl:block space-y-4">
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <h3 className="mb-3 text-xs font-semibold text-foreground">Info</h3>
          <p className="text-[10px] leading-relaxed text-muted-foreground">
            Select or create a pipeline to generate AI content. Each pipeline runs through 8 stages of automated content creation.
          </p>
        </div>
      </div>
    </div>
  );
}
