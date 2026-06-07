import api from './api';

export interface Project {
  id: string;
  topic: string;
  title: string;
  points_to_cover: string[];
  tone: string;
  content_type: string;
  target_audience: string | null;
  seo_keywords: string[];
  status: string;
  outline: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectResponse {
  id: string;
  topic: string;
  title: string;
  points_to_cover: string[];
  tone: string;
  content_type: string;
  target_audience: string | null;
  seo_keywords: string[];
  status: string;
  outline: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  description: string | null;
  archived: boolean;
  total_outputs: number;
  total_memories: number;
  last_activity: string | null;
}

function toProjectSummary(r: ProjectResponse): ProjectSummary {
  return {
    id: r.id,
    name: r.title || r.topic,
    description: r.topic,
    archived: false,
    total_outputs: 0,
    total_memories: 0,
    last_activity: r.updated_at,
  };
}

export interface ProjectDashboard {
  project: Record<string, any>;
  total_outputs: number;
  total_memories: number;
  total_sources: number;
  total_tokens_used: number;
  total_cost: number;
  last_activity: string | null;
  recent_workflows: any[];
  instructions_count?: number;
  skills_count?: number;
  allowed_sources_count?: number;
  blocked_sources_count?: number;
  chat_sessions_count?: number;
}

export interface Memory {
  id: string;
  project_id: string;
  memory_type: string;
  content: string;
  confidence_score: number;
  pinned: boolean;
  priority: number;
  created_at: string;
}

export interface Output {
  id: string;
  project_id: string;
  workflow_execution_id: string | null;
  title: string | null;
  content: string | null;
  content_type: string;
  created_at: string;
}

export interface TimelineEntry {
  id: string;
  type: 'prompt' | 'output' | 'memory' | 'workflow';
  title: string;
  description: string | null;
  created_at: string;
  metadata: Record<string, any>;
}

export interface ContextAssembly {
  project_context: {
    relevant_memories: Array<{ type: string; content: string; similarity: number; pinned: boolean }>;
    pinned_knowledge: Array<{ type: string; content: string; priority: number }>;
    related_outputs: Array<{ title: string | null; content_type: string; content_preview: string | null }>;
    previous_prompts: Array<{ prompt: string }>;
  };
  prompt: string;
  relevant_memories: Memory[];
  pinned_memories: Memory[];
  related_outputs: Output[];
  related_prompts: any[];
}

export const projectApi = {
  async list(includeArchived = false): Promise<ProjectSummary[]> {
    const params = new URLSearchParams({ include_archived: String(includeArchived) });
    const response = await api.get<ProjectResponse[]>(`/projects?${params}`);
    return (response.data ?? []).map(toProjectSummary);
  },

  async get(projectId: string): Promise<Project> {
    const response = await api.get<Project>(`/projects/${projectId}`);
    return response.data;
  },

  async create(name: string, description?: string): Promise<Project> {
    const response = await api.post<ProjectResponse>('/projects', { topic: name, title: name, points_to_cover: [] });
    return response.data;
  },

  async update(projectId: string, data: { name?: string; description?: string; archived?: boolean }): Promise<Project> {
    const response = await api.put<Project>(`/projects/${projectId}`, data);
    return response.data;
  },

  async delete(projectId: string): Promise<void> {
    await api.delete(`/projects/${projectId}`);
  },

  async getDashboard(projectId: string): Promise<ProjectDashboard> {
    const response = await api.get<ProjectDashboard>(`/projects/${projectId}/dashboard`);
    return response.data;
  },

  async getTimeline(projectId: string, limit = 50, offset = 0): Promise<TimelineEntry[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    const response = await api.get<TimelineEntry[]>(`/projects/${projectId}/timeline?${params}`);
    return response.data;
  },

  async getMemories(projectId: string, memoryType?: string, limit = 50, offset = 0): Promise<Memory[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (memoryType) params.append('memory_type', memoryType);
    const response = await api.get<Memory[]>(`/projects/${projectId}/memories?${params}`);
    return response.data;
  },

  async getOutputs(projectId: string, contentType?: string, limit = 50, offset = 0): Promise<Output[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (contentType) params.append('content_type', contentType);
    const response = await api.get<Output[]>(`/projects/${projectId}/outputs?${params}`);
    return response.data;
  },

  async searchMemories(
    projectId: string,
    query: string,
    topK = 10,
    threshold = 0.0,
    memoryType?: string
  ): Promise<{ results: Memory[]; query: string; total: number }> {
    const response = await api.post<{ results: Memory[]; query: string; total: number }>(
      `/projects/${projectId}/memory/search`,
      { query, top_k: topK, similarity_threshold: threshold, memory_type: memoryType || null }
    );
    return response.data;
  },

  async pinMemory(projectId: string, memoryId: string, priority = 0): Promise<void> {
    await api.post(`/projects/${projectId}/memory/pin`, { memory_id: memoryId, priority });
  },

  async deleteMemory(projectId: string, memoryId: string): Promise<void> {
    await api.delete(`/projects/${projectId}/memory/${memoryId}`);
  },

  async assembleContext(
    projectId: string,
    prompt: string,
    topK = 10,
    threshold = 0.0
  ): Promise<ContextAssembly> {
    const response = await api.post<ContextAssembly>(`/projects/${projectId}/context`, {
      project_id: projectId,
      prompt,
      top_k: topK,
      similarity_threshold: threshold,
    });
    return response.data;
  },
};