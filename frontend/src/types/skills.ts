export interface Skill {
  id: string;
  name: string;
  description: string | null;
  content_markdown: string;
  category: SkillCategory;
  version: number;
  created_at: string;
  updated_at: string;
  created_by: string | null;
  active: boolean;
  agent_targets: string[];
}

export type SkillCategory = 'writing' | 'research' | 'seo' | 'fact_check' | 'compliance' | 'brand_voice' | 'youtube' | 'finance' | 'custom';

export interface SkillVersion {
  id: string;
  skill_id: string;
  version: number;
  content_markdown: string;
  created_at: string;
  created_by: string | null;
}

export interface ProjectSkill {
  id: string;
  project_id: string;
  skill_id: string;
  skill_name: string;
  skill_category: string;
  priority: number;
  enabled: boolean;
}

export interface SkillTestResult {
  prompt: string;
  without_skill: string;
  with_skill: string;
  compliance_score: number;
  readability_diff: number;
  seo_diff: number;
  style_diff: number;
}

export interface SkillAnalytics {
  skill_id: string;
  usage_count: number;
  average_compliance: number;
  average_rating: number;
  last_used: string | null;
}

export interface SkillTemplate {
  id: string;
  name: string;
  category: string;
  description: string | null;
  content_markdown: string;
  author: string | null;
  downloads: number;
  created_at: string;
}
