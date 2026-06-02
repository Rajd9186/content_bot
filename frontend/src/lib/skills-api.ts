import api from './api';
import type { Skill, SkillCategory, SkillVersion, ProjectSkill, SkillTestResult, SkillAnalytics, SkillTemplate } from '@/types/skills';

export type { Skill, SkillCategory };

export const skillsApi = {
  async list(category?: string, activeOnly = true): Promise<Skill[]> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    params.append('active_only', String(activeOnly));
    const response = await api.get<Skill[]>(`/skills?${params}`);
    return response.data;
  },

  async get(id: string): Promise<Skill> {
    const response = await api.get<Skill>(`/skills/${id}`);
    return response.data;
  },

  async create(data: { name: string; content_markdown: string; category: string; description?: string; agent_targets?: string[] }): Promise<Skill> {
    const response = await api.post<Skill>('/skills', data);
    return response.data;
  },

  async update(id: string, data: { name?: string; content_markdown?: string; category?: string; description?: string; active?: boolean; agent_targets?: string[] }): Promise<Skill> {
    const response = await api.put<Skill>(`/skills/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/skills/${id}`);
  },

  async getVersions(id: string): Promise<SkillVersion[]> {
    const response = await api.get<SkillVersion[]>(`/skills/${id}/versions`);
    return response.data;
  },

  async rollback(id: string, version: number): Promise<Skill> {
    const params = new URLSearchParams({ version: String(version) });
    const response = await api.post<Skill>(`/skills/${id}/rollback?${params}`);
    return response.data;
  },

  async getProjectSkills(projectId: string): Promise<ProjectSkill[]> {
    const response = await api.get<ProjectSkill[]>(`/projects/${projectId}/skills`);
    return response.data;
  },

  async assignToProject(projectId: string, skillId: string, priority?: number): Promise<ProjectSkill> {
    const response = await api.post<ProjectSkill>(`/projects/${projectId}/skills`, { skill_id: skillId, priority });
    return response.data;
  },

  async removeFromProject(projectId: string, skillId: string): Promise<void> {
    await api.delete(`/projects/${projectId}/skills/${skillId}`);
  },

  async updateProjectSkill(projectId: string, skillId: string, data: { priority?: number; enabled?: boolean }): Promise<void> {
    await api.put(`/projects/${projectId}/skills/${skillId}`, data);
  },

  async test(data: { prompt: string; skill_id: string }): Promise<SkillTestResult> {
    const response = await api.post<SkillTestResult>('/skills/test', data);
    return response.data;
  },

  async getAnalytics(id: string): Promise<SkillAnalytics> {
    const response = await api.get<SkillAnalytics>(`/skills/${id}/analytics`);
    return response.data;
  },

  async getTopSkills(): Promise<SkillAnalytics[]> {
    const response = await api.get<SkillAnalytics[]>('/skills/analytics/top');
    return response.data;
  },

  async listTemplates(category?: string): Promise<SkillTemplate[]> {
    const params = category ? new URLSearchParams({ category }) : '';
    const response = await api.get<SkillTemplate[]>(`/skills/templates${params ? `?${params}` : ''}`);
    return response.data;
  },

  async createTemplate(data: { name: string; category: string; content_markdown: string; description?: string }): Promise<SkillTemplate> {
    const response = await api.post<SkillTemplate>('/skills/templates', data);
    return response.data;
  },

  async cloneToTemplate(skillId: string): Promise<SkillTemplate> {
    const response = await api.post<SkillTemplate>(`/skills/${skillId}/clone-template`);
    return response.data;
  },

  async getProviderStats(): Promise<Record<string, any>> {
    const response = await api.get<Record<string, any>>("/api/providers/stats");
    return response.data;
  },
};
