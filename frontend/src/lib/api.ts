import type {
  Project,
  ProjectCreate,
  GeneratedContent,
  ContentGenerateResponse,
  VerificationDashboard,
  EvidenceItem,
  WorkflowExecution,
  WorkflowTelemetry,
  Contradiction,
  HyperlinkValidation,
  HyperlinkSummary,
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_URL}${path}`
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Request failed: ${response.statusText}`)
  }

  return response.json()
}

export const api = {
  projects: {
    create: (data: ProjectCreate) =>
      request<Project>('/projects', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    quickCreate: (topic: string) =>
      request<Project>('/projects/quick', {
        method: 'POST',
        body: JSON.stringify({ topic }),
      }),

    list: (skip = 0, limit = 100) =>
      request<Project[]>(`/projects?skip=${skip}&limit=${limit}`),

    get: (id: string) =>
      request<Project>(`/projects/${id}`),

    delete: (id: string) =>
      request<void>(`/projects/${id}`, { method: 'DELETE' }),
  },

  content: {
    getLatest: (projectId: string) =>
      request<GeneratedContent>(`/projects/${projectId}/content/latest`),

    generate: (projectId: string, mode = 'v2') =>
      request<ContentGenerateResponse>(`/projects/${projectId}/content/generate?mode=${mode}`, {
        method: 'POST',
      }),
  },

  evidence: {
    list: (projectId: string) =>
      request<{ evidence: EvidenceItem[]; total_count: number; average_relevance: number }>(
        `/projects/${projectId}/evidence`
      ),
  },

  verification: {
    getDashboard: (projectId: string) =>
      request<VerificationDashboard>(`/projects/${projectId}/verification/dashboard`),

    getClaims: (projectId: string) =>
      request<{
        claims: any[]
        total_claims: number
        verified_count: number
        unverified_count: number
        contradicted_count: number
        unsupported_count: number
        average_confidence: number
      }>(`/projects/${projectId}/verification/claims`),

    getSources: (projectId: string) =>
      request<{ sources: any[]; total_sources: number; average_trust_score: number }>(
        `/projects/${projectId}/verification/sources`
      ),
  },

  workflow: {
      get: (projectId: string) =>
        request<WorkflowExecution | null>(`/projects/${projectId}/workflow`),

      getTelemetry: (projectId: string) =>
        request<WorkflowTelemetry>(`/projects/${projectId}/workflow/telemetry`),

      getContradictions: (projectId: string) =>
        request<Contradiction[]>(`/projects/${projectId}/workflow/contradictions`),

      resolveContradiction: (projectId: string, contradictionId: string, resolution: string) =>
        request<Contradiction>(`/projects/${projectId}/workflow/contradictions/${contradictionId}/resolve`, {
          method: 'POST',
          body: JSON.stringify({ resolution }),
        }),

      getHyperlinks: (projectId: string) =>
        request<HyperlinkValidation[]>(`/projects/${projectId}/workflow/hyperlinks`),

      getHyperlinkSummary: (projectId: string) =>
        request<HyperlinkSummary>(`/projects/${projectId}/workflow/hyperlinks/summary`),
  },

  chat: {
    send: (projectId: string, message: string, history: any[]) =>
      request<{ content: string; tool_calls: any[] }>(`/projects/${projectId}/chat`, {
        method: 'POST',
        body: JSON.stringify({ message, history }),
      }),

    getEvents: (projectId: string) =>
      request<any[]>(`/projects/${projectId}/chat/events`),
  },
}
