'use client';

import { useState, useEffect } from 'react';
import { useSkillsStore } from '@/store/skills-store';
import { skillsApi } from '@/lib/skills-api';
import type { Skill, SkillCategory } from '@/types/skills';
import { BookOpen, Plus, Search, Filter, Check, X, Eye, ArrowLeft, Trash2, History } from 'lucide-react';

const categoryColors: Record<string, string> = {
  writing: 'border-blue-700 bg-blue-900/10',
  research: 'border-purple-700 bg-purple-900/10',
  seo: 'border-green-700 bg-green-900/10',
  fact_check: 'border-red-700 bg-red-900/10',
  compliance: 'border-yellow-700 bg-yellow-900/10',
  brand_voice: 'border-pink-700 bg-pink-900/10',
  youtube: 'border-orange-700 bg-orange-900/10',
  finance: 'border-cyan-700 bg-cyan-900/10',
  custom: 'border-gray-700 bg-gray-900/10',
};

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

const AGENT_OPTIONS = ['research_agent', 'writer_agent', 'seo_agent', 'fact_checker_agent', 'compliance_agent'];

export function SkillsDashboard() {
  const { filterCategory, setFilterCategory } = useSkillsStore();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [viewingSkill, setViewingSkill] = useState<Skill | null>(null);
  const [versions, setVersions] = useState<{ id: string; version: number; created_at: string }[]>([]);
  const [showVersions, setShowVersions] = useState(false);

  useEffect(() => {
    loadSkills();
  }, [filterCategory]);

  const loadSkills = async () => {
    setLoading(true);
    try {
      const data = await skillsApi.list(
        filterCategory === 'all' ? undefined : filterCategory
      );
      setSkills(data);
    } catch (err) {
      console.error('Failed to load skills:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredSkills = skills.filter((s) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (s.description && s.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleCreate = async (data: {
    name: string;
    description: string;
    category: string;
    content_markdown: string;
    agent_targets: string[];
  }) => {
    try {
      await skillsApi.create(data);
      setShowCreateModal(false);
      loadSkills();
    } catch (err) {
      console.error('Failed to create skill:', err);
    }
  };

  const handleUpdate = async (id: string, data: {
    name?: string;
    description?: string;
    category?: string;
    content_markdown?: string;
    agent_targets?: string[];
  }) => {
    try {
      await skillsApi.update(id, data);
      setEditingSkill(null);
      setViewingSkill(null);
      loadSkills();
    } catch (err) {
      console.error('Failed to update skill:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this skill? This action cannot be undone.')) return;
    try {
      await skillsApi.delete(id);
      setViewingSkill(null);
      loadSkills();
    } catch (err) {
      console.error('Failed to delete skill:', err);
    }
  };

  const handleViewVersions = async (id: string) => {
    try {
      const data = await skillsApi.getVersions(id);
      setVersions(data);
      setShowVersions(true);
    } catch (err) {
      console.error('Failed to load versions:', err);
    }
  };

  const resetCreateForm = () => {
    setShowCreateModal(false);
    setEditingSkill(null);
    setViewingSkill(null);
    setShowVersions(false);
    setVersions([]);
  };

  return (
    <div className="p-6 space-y-4 h-full overflow-y-auto">
      {viewingSkill && !editingSkill ? (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <button
              onClick={() => { setViewingSkill(null); setShowVersions(false); }}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-300 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleViewVersions(viewingSkill.id)}
                className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-gray-300 transition-colors flex items-center gap-2"
              >
                <History className="w-4 h-4" />
                Versions
              </button>
              <button
                onClick={() => setEditingSkill(viewingSkill)}
                className="px-3 py-1.5 text-sm bg-emerald-600 hover:bg-emerald-700 rounded text-white transition-colors flex items-center gap-2"
              >
                <Eye className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => handleDelete(viewingSkill.id)}
                className="px-3 py-1.5 text-sm bg-red-700 hover:bg-red-800 rounded text-white transition-colors flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold text-white">{viewingSkill.name}</h2>
              <span className={`px-2 py-0.5 text-xs rounded border ${categoryColors[viewingSkill.category] || categoryColors.custom} text-gray-200`}>
                {CATEGORY_LABELS[viewingSkill.category] || viewingSkill.category}
              </span>
              <span className="px-2 py-0.5 text-xs rounded bg-gray-800 border border-gray-700 text-gray-400">
                v{viewingSkill.version}
              </span>
              <span className={`flex items-center gap-1 text-xs ${viewingSkill.active ? 'text-emerald-400' : 'text-gray-500'}`}>
                <span className={`w-2 h-2 rounded-full ${viewingSkill.active ? 'bg-emerald-400' : 'bg-gray-600'}`} />
                {viewingSkill.active ? 'Active' : 'Inactive'}
              </span>
            </div>
            {viewingSkill.description && (
              <p className="text-gray-400 mb-4">{viewingSkill.description}</p>
            )}
            {viewingSkill.agent_targets && viewingSkill.agent_targets.length > 0 && (
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs text-gray-500">Targets:</span>
                {viewingSkill.agent_targets.map((target) => (
                  <span key={target} className="px-2 py-0.5 text-xs rounded bg-gray-800 border border-gray-700 text-gray-300">
                    {target}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="bg-gray-900 rounded-lg border border-gray-700 p-4">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Skill Content</h3>
            <pre className="text-sm text-gray-200 whitespace-pre-wrap font-mono bg-gray-950 p-4 rounded border border-gray-800 max-h-96 overflow-y-auto">
              {viewingSkill.content_markdown}
            </pre>
          </div>

          {showVersions && (
            <div className="bg-gray-900 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-300">Version History</h3>
                <button onClick={() => setShowVersions(false)} className="text-gray-500 hover:text-white">
                  <X className="w-4 h-4" />
                </button>
              </div>
              {versions.length === 0 ? (
                <p className="text-sm text-gray-500">No version history available.</p>
              ) : (
                <div className="space-y-2">
                  {versions.map((v) => (
                    <div key={v.id} className="flex items-center justify-between p-2 bg-gray-800 rounded">
                      <span className="text-sm text-gray-300">v{v.version}</span>
                      <span className="text-xs text-gray-500">{new Date(v.created_at).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-emerald-400" />
              Skills Engine
            </h2>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded text-sm text-white transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Skill
            </button>
          </div>

          <div className="flex gap-3">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value as SkillCategory | 'all')}
                className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="all">All Categories</option>
                {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search skills..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {loading ? (
            <div className="text-center text-gray-500 py-12">
              <p>Loading skills...</p>
            </div>
          ) : filteredSkills.length === 0 ? (
            <div className="text-center text-gray-500 py-12 border border-dashed border-gray-700 rounded-lg">
              <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-600" />
              <p>No skills found. Create your first skill to get started.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredSkills.map((skill) => {
                const colorClass = categoryColors[skill.category] || categoryColors.custom;
                return (
                  <div
                    key={skill.id}
                    onClick={() => setViewingSkill(skill)}
                    className={`p-4 rounded-lg border ${colorClass} cursor-pointer hover:brightness-110 transition-all`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="text-xs font-medium text-gray-300 uppercase truncate">
                          {CATEGORY_LABELS[skill.category] || skill.category}
                        </span>
                        <span className="px-1.5 py-0.5 text-xs rounded bg-gray-800 border border-gray-700 text-gray-500 shrink-0">
                          v{skill.version}
                        </span>
                      </div>
                      <span className={`flex items-center gap-1 text-xs shrink-0 ${skill.active ? 'text-emerald-400' : 'text-gray-500'}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${skill.active ? 'bg-emerald-400' : 'bg-gray-600'}`} />
                        {skill.active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <h3 className="text-sm font-semibold text-white mb-1 truncate">{skill.name}</h3>
                    {skill.description && (
                      <p className="text-xs text-gray-400 line-clamp-2">{skill.description}</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {(showCreateModal || editingSkill) && (
        <SkillFormModal
          initialData={editingSkill}
          onSave={(data) => {
            if (editingSkill) {
              handleUpdate(editingSkill.id, data);
            } else {
              handleCreate(data as any);
            }
          }}
          onClose={resetCreateForm}
        />
      )}
    </div>
  );
}

function SkillFormModal({
  initialData,
  onSave,
  onClose,
}: {
  initialData: Skill | null;
  onSave: (data: {
    name: string;
    description?: string;
    category: string;
    content_markdown: string;
    agent_targets: string[];
  }) => void;
  onClose: () => void;
}) {
  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [category, setCategory] = useState<string>(initialData?.category || 'writing');
  const [content, setContent] = useState(initialData?.content_markdown || '');
  const [agentTargets, setAgentTargets] = useState<string[]>(initialData?.agent_targets || []);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !content.trim()) return;
    setSaving(true);
    try {
      await onSave({ name, description, category, content_markdown: content, agent_targets: agentTargets });
    } finally {
      setSaving(false);
    }
  };

  const toggleAgentTarget = (target: string) => {
    setAgentTargets((prev) =>
      prev.includes(target) ? prev.filter((t) => t !== target) : [...prev, target]
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 rounded-lg border border-gray-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white">
            {initialData ? 'Edit Skill' : 'Create Skill'}
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Skill name..."
              required
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description..."
              rows={2}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:border-emerald-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:border-emerald-500"
            >
              {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Skill Content (Markdown)</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={`# Skill Name\n\n## Purpose\nDescribe what this skill does...\n\n## Guidelines\n- Rule one\n- Rule two\n\n## Examples\n* Example input/output`}
              rows={12}
              required
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:border-emerald-500 font-mono resize-y"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Agent Targets (optional)</label>
            <div className="grid grid-cols-2 gap-2">
              {AGENT_OPTIONS.map((agent) => (
                <label
                  key={agent}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 cursor-pointer hover:border-gray-600 transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={agentTargets.includes(agent)}
                    onChange={() => toggleAgentTarget(agent)}
                    className="rounded bg-gray-700 border-gray-600 text-emerald-500 focus:ring-emerald-500"
                  />
                  {agent.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || !name.trim() || !content.trim()}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 rounded text-sm text-white transition-colors flex items-center gap-2"
            >
              <Check className="w-4 h-4" />
              {saving ? 'Saving...' : initialData ? 'Update Skill' : 'Create Skill'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
