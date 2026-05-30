"use client";

import { usePipelineStore } from "@/store/pipeline-store";

export function usePipeline() {
  const store = usePipelineStore();
  return {
    pipelines: store.pipelines,
    currentId: store.currentId,
    status: store.status,
    content: store.content,
    timeline: store.timeline,
    events: store.events,
    loading: store.loading,
    error: store.error,
    sseStatus: store.sseStatus,
    create: store.create,
    run: store.run,
    cancel: store.cancel,
    review: store.review,
    select: store.select,
    refresh: store.refresh,
    refreshContent: store.refreshContent,
    refreshTimeline: store.refreshTimeline,
    addEvent: store.addEvent,
    clearEvents: store.clearEvents,
    setSSEStatus: store.setSSEStatus,
    setSSEError: store.setSSEError,
  };
}
