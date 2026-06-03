export interface HealthStatus {
  status: string;
  version: string;
  uptimeSeconds: number;
}

export interface ReadinessStatus {
  status: string;
  checks: Record<string, string>;
}

export interface PipelineStartResponse {
  workflow_id: string;
  correlation_id: string;
  topic: string;
  status: string;
  message: string;
}

export interface NodeInfo {
  status: string;
  error: string | null;
  tokens_used: number;
  latency_ms: number;
  actions: AgentAction[];
  output: Record<string, unknown>;
  retry_count: number;
  started_at: string | null;
  completed_at: string | null;
}

export interface AgentAction {
  action: string;
  timestamp: string;
  details: string;
  success?: boolean;
}

export interface PipelineStatusResponse {
  workflow_id: string;
  workspace_id: string;
  topic: string;
  current_node: string;
  status: string;
  has_failures: boolean;
  draft_preview: string;
  final_content: string;
  needs_review: boolean;
  review: Record<string, unknown> | null;
  nodes: Record<string, NodeInfo>;
  research_summary: string;
  seo_keywords: string[];
  error_count: number;
  created_at: string;
  updated_at: string;
}

export interface PipelineContentResponse {
  workflow_id: string;
  topic: string;
  final_content: string;
  draft_content: string | null;
  word_count: number;
  metadata: Record<string, unknown>;
}

export interface TimelineEntry {
  node: string;
  status: string;
  started_at: string;
  completed_at: string;
  latency_ms: number;
  tokens_used: number;
  error: string | null;
  actions: AgentAction[];
}

export interface PipelineTimelineResponse {
  workflow_id: string;
  timeline: TimelineEntry[];
}

export interface PipelineSSEEvent {
  type: string;
  node?: string;
  status?: string;
  tokens_used?: number;
  latency_ms?: number;
  error?: string | null;
  workflow_id?: string;
  actions?: AgentAction[];
  started_at?: string | null;
  completed_at?: string | null;
}

export interface WorkflowResponse {
  id: string;
  name: string;
  status: string;
  stages: string[];
  config: Record<string, unknown>;
  created_at: string;
}

export interface JobResponse {
  id: string;
  workflow_id: string;
  status: string;
  progress: number;
  error: string | null;
  created_at: string;
}

export interface ContentItem {
  id: string;
  title: string;
  slug: string;
  status: string;
  version: number;
}

export interface WorkspaceMember {
  id: string;
  email: string;
  role: "admin" | "user" | "viewer";
  name: string;
  joined_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key: string;
  created_at: string;
  last_used: string | null;
  usage_count: number;
}

export interface AnalyticsSummary {
  totalPipelines: number;
  successRate: number;
  avgExecutionTimeMs: number;
  totalTokens: number;
  costEstimate: number;
}

export interface AgentMetrics {
  name: string;
  status: string;
  successRate: number;
  avgTokens: number;
  avgLatencyMs: number;
  executions: number;
  model: string;
}

export interface ProviderHealthStatus {
  provider: string;
  status: "healthy" | "degraded" | "down" | "circuit_open";
  model: string;
  rateLimit: { remaining: number; limit: number; resetsInMs: number } | null;
  circuitBreaker?: {
    state: "closed" | "open" | "half_open";
    failureCount: number;
    threshold: number;
    resetTimeoutMs: number;
  };
  uptimeMs?: number;
}

export type AgentName =
  | "research"
  | "planner"
  | "writer"
  | "seo"
  | "fact_checker"
  | "compliance"
  | "human_review"
  | "finalizer";

export const AGENT_LABELS: Record<AgentName, string> = {
  research: "Research",
  planner: "Planner",
  writer: "Writer",
  seo: "SEO",
  fact_checker: "Fact Checker",
  compliance: "Compliance",
  human_review: "Human Review",
  finalizer: "Finalizer",
};

export const AGENT_ORDER: AgentName[] = [
  "research",
  "planner",
  "writer",
  "seo",
  "fact_checker",
  "compliance",
  "human_review",
  "finalizer",
];

export type SectionName =
  | "pipeline"
  | "history"
  | "projects"
  | "analytics"
  | "workspace"
  | "settings"
  | "agents"
  | "orchestration"
  | "metrics"
  | "skills"
  | "operations";

export interface SettingsState {
  apiBaseUrl: string;
  refreshInterval: number;
  telemetryEnabled: boolean;
  defaultTone: string;
  defaultAudience: string;
}

export interface UserProfile {
  name: string;
  email: string;
  avatar?: string;
  role: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}
