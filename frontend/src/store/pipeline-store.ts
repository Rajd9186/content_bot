import { create } from "zustand";
import type {
  PipelineStartResponse,
  PipelineStatusResponse,
  PipelineContentResponse,
  PipelineTimelineResponse,
  PipelineSSEEvent,
} from "@/types/api";
import { apiGet, apiPost } from "@/lib/api";

interface PipelineEntry {
  workflow_id: string;
  topic: string;
  status: string;
  created_at: string;
  total_tokens?: number;
  total_latency?: number;
}

interface PipelineState {
  pipelines: PipelineEntry[];
  currentId: string | null;
  status: PipelineStatusResponse | null;
  content: PipelineContentResponse | null;
  timeline: PipelineTimelineResponse | null;
  events: PipelineSSEEvent[];
  loading: boolean;
  error: string | null;
  sseStatus: "disconnected" | "connecting" | "connected";
  sseError: string | null;
  create: (topic: string, audience?: string, tone?: string, goals?: string) => Promise<string>;
  run: (id: string) => Promise<void>;
  refresh: (id: string) => Promise<void>;
  refreshContent: (id: string) => Promise<void>;
  refreshTimeline: (id: string) => Promise<void>;
  cancel: (id: string) => Promise<void>;
  review: (id: string, action: string, comments?: string) => Promise<void>;
  select: (id: string) => Promise<void>;
  addEvent: (event: PipelineSSEEvent) => void;
  clearEvents: () => void;
  setSSEStatus: (status: "disconnected" | "connecting" | "connected") => void;
  setSSEError: (error: string | null) => void;
}

export const usePipelineStore = create<PipelineState>((set, get) => ({
  pipelines: [],
  currentId: null,
  status: null,
  content: null,
  timeline: null,
  events: [],
  loading: false,
  error: null,
  sseStatus: "disconnected",
  sseError: null,

  create: async (topic, audience = "general", tone = "professional", goals = "") => {
    set({ loading: true, error: null });
    try {
      const result = await apiPost<PipelineStartResponse>(
        "/content-pipeline/pipeline/start",
        undefined,
        { topic, audience, tone, goals, workspace_id: "default" },
      );
      set((s) => ({
        pipelines: [
          ...s.pipelines,
          {
            workflow_id: result.workflow_id,
            topic: result.topic,
            status: result.status,
            created_at: new Date().toISOString(),
          },
        ],
        currentId: result.workflow_id,
        loading: false,
      }));
      return result.workflow_id;
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : "Create failed" });
      throw e;
    }
  },

  run: async (id) => {
    set({ loading: true, error: null });
    try {
      apiPost<PipelineStatusResponse>(
        `/content-pipeline/pipeline/${id}/run`,
        undefined,
        { skip_review: "true" },
      ).then((result) => {
        set({ status: result, loading: false });
        get().refresh(id);
        get().refreshContent(id);
        get().refreshTimeline(id);
      }).catch((e) => {
        set({ loading: false, error: e instanceof Error ? e.message : "Run failed" });
      });
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : "Run failed" });
    }
  },

  refresh: async (id) => {
    try {
      const result = await apiGet<PipelineStatusResponse>(`/content-pipeline/pipeline/${id}`);
      set((s) => ({
        status: result,
        pipelines: s.pipelines.map((p) =>
          p.workflow_id === id ? { ...p, status: result.status } : p,
        ),
      }));
    } catch (e) {
      set({ error: e instanceof Error ? e.message : "Refresh failed" });
    }
  },

  refreshContent: async (id) => {
    try {
      const result = await apiGet<PipelineContentResponse>(
        `/content-pipeline/pipeline/${id}/content`,
      );
      set({ content: result });
    } catch {}
  },

  refreshTimeline: async (id) => {
    try {
      const result = await apiGet<PipelineTimelineResponse>(
        `/content-pipeline/pipeline/${id}/timeline`,
      );
      set({ timeline: result });
    } catch {}
  },

  cancel: async (id) => {
    try {
      await apiPost(`/content-pipeline/pipeline/${id}/cancel`);
      get().refresh(id);
    } catch {}
  },

  review: async (id, action, comments = "") => {
    try {
      await apiPost(`/content-pipeline/pipeline/${id}/review`, {
        action,
        comments,
        reviewer_id: "dashboard-user",
      });
      get().refresh(id);
    } catch {}
  },

  select: async (id) => {
    set({ currentId: id, loading: true, error: null });
    try {
      const result = await apiGet<PipelineStatusResponse>(
        `/content-pipeline/pipeline/${id}`,
      );
      set({ status: result, currentId: id, loading: false });
      get().refreshContent(id);
      get().refreshTimeline(id);
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : "Load failed" });
    }
  },

  addEvent: (event) => set((s) => ({ events: [...s.events.slice(-99), event] })),
  clearEvents: () => set({ events: [] }),
  setSSEStatus: (sseStatus) => set({ sseStatus }),
  setSSEError: (sseError) => set({ sseError }),
}));
