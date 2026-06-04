'use client';

import { useCallback, useEffect, useState } from 'react';
import { useProjectStore } from '@/store/project-store';
import { skillsApi } from '@/lib/skills-api';
import type { Skill, ProjectSkill } from '@/types/skills';
import { BookOpen, Plus, X, ChevronUp, ChevronDown, Check } from 'lucide-react';

const CATEGORY_LABELS: Record<string, string> = {
  writing: 'Writing',
  research: 'Research',
  seo: 'SEO',
  fact_check: 'Fact Check',
  compliance: 'Compliance',
  brand_voice: 'Brand Voice',
  youtube: 'YouTube',
  finance: 'Finance',
  custom: 'Custom',
};

export function SkillAssignment() {
  const { currentProjectId } = useProjectStore();
  const [projectSkills, setProjectSkills] = useState<ProjectSkill[]>([]);
  const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddPanel, setShowAddPanel] = useState(false);

  useEffect(() => {
    if (!currentProjectId) {
      setProjectSkills([]);
      setAvailableSkills([]);
      return;
    }
    loadData();
  }, [currentProjectId]);

  useEffect(() => {
    if (!showAddPanel) return;
    const handleKeyDown = (e: KeyboardEvent) => { if (e.key === "Escape") setShowAddPanel(false); };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [showAddPanel]);

  const loadData = useCallback(async () => {
    if (!currentProjectId) return;
    setLoading(true);
    try {
      const [assigned, all] = await Promise.all([
        skillsApi.getProjectSkills(currentProjectId),
        skillsApi.list(undefined, false),
      ]);
      setProjectSkills(assigned);
      const assignedIds = new Set(assigned.map((ps) => ps.skill_id));
      setAvailableSkills(all.filter((s) => !assignedIds.has(s.id)));
    } catch (err) {
      console.error('Failed to load skill assignments:', err);
    } finally {
      setLoading(false);
    }
  }, [currentProjectId]);

  const handleAssign = async (skillId: string, priority?: number) => {
    if (!currentProjectId) return;
    try {
      await skillsApi.assignToProject(currentProjectId, skillId, priority);
      setShowAddPanel(false);
      loadData();
    } catch (err) {
      console.error('Failed to assign skill:', err);
    }
  };

  const handleRemove = async (skillId: string) => {
    if (!currentProjectId) return;
    try {
      await skillsApi.removeFromProject(currentProjectId, skillId);
      loadData();
    } catch (err) {
      console.error('Failed to remove skill:', err);
    }
  };

  const handleToggleEnabled = async (skillId: string, enabled: boolean) => {
    if (!currentProjectId) return;
    try {
      await skillsApi.updateProjectSkill(currentProjectId, skillId, { enabled });
      setProjectSkills((prev) =>
        prev.map((ps) => (ps.skill_id === skillId ? { ...ps, enabled } : ps))
      );
    } catch (err) {
      console.error('Failed to toggle skill:', err);
    }
  };

  const handlePriorityChange = async (skillId: string, priority: number) => {
    if (!currentProjectId || priority < 1) return;
    try {
      await skillsApi.updateProjectSkill(currentProjectId, skillId, { priority });
      setProjectSkills((prev) =>
        prev.map((ps) => (ps.skill_id === skillId ? { ...ps, priority } : ps))
      );
    } catch (err) {
      console.error('Failed to update priority:', err);
    }
  };

  if (!currentProjectId) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Select a project to manage skill assignments.</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4 h-full overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-emerald-400" />
          Assigned Skills ({projectSkills.length})
        </h2>
        <button
          onClick={() => setShowAddPanel(true)}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded text-sm text-white transition-colors flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Skill
        </button>
      </div>

      {loading ? (
        <div className="text-center text-gray-500 py-8">
          <p>Loading assignments...</p>
        </div>
      ) : projectSkills.length === 0 ? (
        <div className="text-center text-gray-500 py-12 border border-dashed border-gray-700 rounded-lg">
          <p>No skills assigned to this project.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {projectSkills
            .sort((a, b) => a.priority - b.priority)
            .map((ps) => (
              <div
                key={ps.id}
                className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg border border-gray-700"
              >
                <div className="flex flex-col gap-0.5">
                  <button
                    onClick={() => handlePriorityChange(ps.skill_id, ps.priority + 1)}
                    className="p-0.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
                    title="Increase priority"
                  >
                    <ChevronUp className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handlePriorityChange(ps.skill_id, Math.max(1, ps.priority - 1))}
                    className="p-0.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
                    title="Decrease priority"
                  >
                    <ChevronDown className="w-3 h-3" />
                  </button>
                </div>

                <span className="text-xs font-mono text-gray-500 w-6 text-center">
                  {ps.priority}
                </span>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white truncate">{ps.skill_name}</span>
                    <span className="px-1.5 py-0.5 text-xs rounded bg-gray-900 border border-gray-700 text-gray-400 shrink-0">
                      {CATEGORY_LABELS[ps.skill_category] || ps.skill_category}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => handleToggleEnabled(ps.skill_id, !ps.enabled)}
                  className={`relative w-10 h-5 rounded-full transition-colors ${
                    ps.enabled ? 'bg-emerald-600' : 'bg-gray-700'
                  }`}
                  title={ps.enabled ? 'Disable' : 'Enable'}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      ps.enabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>

                <button
                  onClick={() => handleRemove(ps.skill_id)}
                  className="p-1 hover:bg-red-900/30 rounded text-gray-500 hover:text-red-400 transition-colors"
                  title="Remove skill"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
        </div>
      )}

      {showAddPanel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-skill-title"
        >
          <div className="bg-gray-900 rounded-lg border border-gray-700 w-full max-w-lg max-h-[80vh] overflow-y-auto mx-4">
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h3 id="add-skill-title" className="text-lg font-semibold text-white">Add Skill</h3>
              <button onClick={() => setShowAddPanel(false)} className="text-gray-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {availableSkills.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <p>All skills are already assigned to this project.</p>
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {availableSkills.map((skill) => (
                  <div
                    key={skill.id}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white truncate">{skill.name}</span>
                        <span className="px-1.5 py-0.5 text-xs rounded bg-gray-800 border border-gray-700 text-gray-400 shrink-0">
                          {CATEGORY_LABELS[skill.category] || skill.category}
                        </span>
                      </div>
                      {skill.description && (
                        <p className="text-xs text-gray-500 truncate mt-0.5">{skill.description}</p>
                      )}
                    </div>
                    <button
                      onClick={() => handleAssign(skill.id)}
                      className="px-3 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 rounded text-white transition-colors flex items-center gap-1 shrink-0"
                    >
                      <Check className="w-3 h-3" />
                      Assign
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
