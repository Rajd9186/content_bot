"use client";

import { useEffect, useRef, useCallback } from "react";
import { usePipelineStore } from "@/store/pipeline-store";
import { createSSEConnection } from "@/lib/api";
import type { PipelineSSEEvent } from "@/types/api";

export function useSSE(id: string | null) {
  const refresh = usePipelineStore((s) => s.refresh);
  const refreshContent = usePipelineStore((s) => s.refreshContent);
  const refreshTimeline = usePipelineStore((s) => s.refreshTimeline);
  const addEvent = usePipelineStore((s) => s.addEvent);
  const setSSEStatus = usePipelineStore((s) => s.setSSEStatus);
  const setSSEError = usePipelineStore((s) => s.setSSEError);
  const esRef = useRef<EventSource | null>(null);

  const handleEvent = useCallback(
    (event: PipelineSSEEvent) => {
      addEvent(event);
      if (event.type === "node_completed" || event.type === "pipeline_completed" || event.type === "pipeline_failed") {
        if (id) {
          refresh(id);
          refreshContent(id).catch(() => {});
          refreshTimeline(id).catch(() => {});
        }
      }
    },
    [id, refresh, refreshContent, refreshTimeline, addEvent],
  );

  useEffect(() => {
    if (!id) return;
    setSSEStatus("connecting");
    esRef.current = createSSEConnection(
      `/content-pipeline/pipeline/${id}/events`,
      handleEvent,
      (err) => {
        setSSEStatus("disconnected");
        setSSEError("SSE connection lost");
      },
      () => setSSEStatus("connected"),
    );
    return () => {
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
        setSSEStatus("disconnected");
        setSSEError(null);
      }
    };
  }, [id, handleEvent, setSSEStatus, setSSEError]);
}
