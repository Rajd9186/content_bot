export const API_BASE = "/api/v1";

export const APP_NAME = "AI Content Intelligence Platform";
export const APP_VERSION = "1.0.0";

export const PIPELINE_STAGES = [
  "research", "planner", "writer", "seo",
  "fact_checker", "compliance", "human_review", "finalizer",
] as const;

export const AUDIENCE_OPTIONS = [
  { value: "developers", label: "Developers" },
  { value: "managers", label: "Managers" },
  { value: "marketing", label: "Marketing" },
  { value: "technical_writers", label: "Technical Writers" },
  { value: "executives", label: "Executives" },
  { value: "researchers", label: "Researchers" },
  { value: "general", label: "General Audience" },
];

export const TONE_OPTIONS = [
  { value: "professional", label: "Professional" },
  { value: "casual", label: "Casual" },
  { value: "academic", label: "Academic" },
  { value: "journalistic", label: "Journalistic" },
  { value: "persuasive", label: "Persuasive" },
  { value: "technical", label: "Technical" },
];

export const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  groq: "Groq",
  nvidia: "NVIDIA",
  anthropic: "Anthropic",
  ollama: "Ollama",
};

export const STATUS_COLORS: Record<string, string> = {
  success: "text-emerald-400",
  completed: "text-emerald-400",
  running: "text-blue-400",
  created: "text-blue-400",
  failed: "text-red-400",
  pending: "text-slate-500",
  skipped: "text-amber-400",
  cancelled: "text-slate-400",
};

export const STATUS_BG: Record<string, string> = {
  success: "bg-emerald-500/10 border-emerald-500/20",
  completed: "bg-emerald-500/10 border-emerald-500/20",
  running: "bg-blue-500/10 border-blue-500/20",
  created: "bg-blue-500/10 border-blue-500/20",
  failed: "bg-red-500/10 border-red-500/20",
  pending: "bg-slate-500/10 border-slate-500/20",
  skipped: "bg-amber-500/10 border-amber-500/20",
};
