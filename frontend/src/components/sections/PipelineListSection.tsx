"use client";

import dynamic from "next/dynamic";

const PipelineHistory = dynamic(() => import("@/components/pipeline/PipelineHistory").then((m) => ({ default: m.PipelineHistory })), { ssr: false });

export function PipelineListSection() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-foreground">Pipeline History</h2>
      </div>
      <PipelineHistory />
    </div>
  );
}
