"use client";

import { useState, useCallback, useRef } from "react";
import {
  BookOpen, Check, ChevronDown, ChevronRight, Clock, Eye,
  FileText, FlaskConical, GitBranch, History, Plus, RefreshCw,
  Save, Search, Sparkles, Tag, ToggleLeft, ToggleRight, Trash2,
  X, AlertTriangle
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSkillsStore } from "@/store/skills-store";
import { skillsApi } from "@/lib/skills-api";
import type { Skill } from "@/types/skills";

const CATEGORY_LABELS: Record<string, string> = {
  writing: "Writing",
  research: "Research",
  seo: "SEO",
  fact_check: "Fact Check",
  compliance: "Compliance",
  brand_voice: "Brand Voice",
  youtube: "YouTube",
  finance: "Finance",
  custom: "Custom",
};

const CATEGORY_COLORS: Record<string, string> = {
  writing: "text-blue-400",
  research: "text-violet-400",
  seo: "text-emerald-400",
  fact_check: "text-red-400",
  compliance: "text-amber-400",
  brand_voice: "text-pink-400",
  youtube: "text-orange-400",
  finance: "text-cyan-400",
  custom: "text-muted-foreground",
};

const CATEGORY_BG: Record<string, string> = {
  writing: "bg-blue-500/10 text-blue-400",
  research: "bg-violet-500/10 text-violet-400",
  seo: "bg-emerald-500/10 text-emerald-400",
  fact_check: "bg-red-500/10 text-red-400",
  compliance: "bg-amber-500/10 text-amber-400",
  brand_voice: "bg-pink-500/10 text-pink-400",
  youtube: "bg-orange-500/10 text-orange-400",
  finance: "bg-cyan-500/10 text-cyan-400",
  custom: "bg-secondary text-muted-foreground",
};

function renderMarkdown(content: string): string {
  if (!content) return "";
  let html = content
    .replace(/^### (.+)$/gm, '<h3 class="text-sm font-semibold text-foreground mt-4 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-base font-semibold text-foreground mt-4 mb-2">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-lg font-bold text-foreground mt-4 mb-2">$1</h1>')
    .replace(/^\* (.+)$/gm, '<li class="flex items-start gap-2 text-xs text-foreground/80 mb-1"><span class="text-emerald-400 shrink-0 mt-1">•</span><span>$1</span></li>')
    .replace(/^- (.+)$/gm, '<li class="flex items-start gap-2 text-xs text-foreground/80 mb-1"><span class="text-muted-foreground/60 shrink-0 mt-1">–</span><span>$1</span></li>')
    .replace(/^\d+\. (.+)$/gm, '<li class="flex items-start gap-2 text-xs text-foreground/80 mb-1 ml-4"><span class="text-violet-400 shrink-0">$&</span></li>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-foreground">$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="font-mono text-[11px] bg-secondary/60 px-1.5 py-0.5 rounded text-violet-400">$1</code>')
    .replace(/\n\n/g, '</p><p class="text-xs text-foreground/80 leading-relaxed mb-2">')
    .replace(/\n/g, "<br>");
  return `<p class="text-xs text-foreground/80 leading-relaxed mb-2">${html}</p>`;
}

interface SkillEditorPanelProps {
  skill: Skill | null;
  isNew: boolean;
  onSave: (data: { name: string; description?: string; category: string; content_markdown: string; agent_targets: string[] }) => void;
  onCancel: () => void;
  onDelete?: () => void;
}

function SkillEditorPanel({ skill, isNew, onSave, onCancel, onDelete }: SkillEditorPanelProps) {
  const [name, setName] = useState(skill?.name || "");
  const [description, setDescription] = useState(skill?.description || "");
  const [category, setCategory] = useState<string>(skill?.category || "writing");
  const [content, setContent] = useState(skill?.content_markdown || "");
  const [agentTargets, setAgentTargets] = useState<string[]>(skill?.agent_targets || []);
  const [activePreviewTab, setActivePreviewTab] = useState<"preview" | "compliance">("preview");
  const [saving, setSaving] = useState(false);

  const AGENT_OPTIONS = [
    { id: "research_agent", label: "Research Agent" },
    { id: "writer_agent", label: "Writer Agent" },
    { id: "seo_agent", label: "SEO Agent" },
    { id: "fact_checker_agent", label: "Fact Checker" },
    { id: "compliance_agent", label: "Compliance Agent" },
  ];

  const toggleAgent = (id: string) => {
    setAgentTargets((prev) => prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]);
  };

  const handleSave = async () => {
    if (!name.trim() || !content.trim()) return;
    setSaving(true);
    try {
      await onSave({ name, description, category, content_markdown: content, agent_targets: agentTargets });
    } finally {
      setSaving(false);
    }
  };

  const wordCount = content.split(/\s+/).filter(Boolean).length;
  const lineCount = content.split("\n").length;

  const complianceItems = [
    { rule: "Has clear section headers (##)", pass: content.includes("##") },
    { rule: "Has guidelines (# ##)", pass: content.includes("#") && content.includes("##") },
    { rule: "Uses bullet points for lists", pass: content.includes("* ") || content.includes("- ") },
    { rule: "Has example section", pass: content.toLowerCase().includes("example") },
    { rule: "Content is at least 100 words", pass: wordCount >= 100 },
    { rule: "Has role definition", pass: content.toLowerCase().includes("role") || content.toLowerCase().includes("you are") || content.toLowerCase().includes("you act as") },
  ];
  const complianceScore = Math.round((complianceItems.filter((i) => i.pass).length / complianceItems.length) * 100);

  if (!skill && !isNew) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <BookOpen className="h-12 w-12 text-muted-foreground/20 mx-auto mb-4" />
          <h3 className="text-sm font-semibold text-foreground mb-1">No skill selected</h3>
          <p className="text-xs text-muted-foreground">Select a skill from the library or create a new one</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 border-b border-border px-4 py-3 flex-shrink-0">
        <div className="flex-1">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Skill name..."
            className="w-full bg-transparent text-sm font-bold text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
          {skill && (
            <div className="flex items-center gap-2 mt-0.5">
              <span className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded", CATEGORY_BG[category])}>
                {CATEGORY_LABELS[category] || category}
              </span>
              <span className="text-[10px] text-muted-foreground">v{skill.version}</span>
              <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                {skill.active
                  ? <><span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Active</>
                  : <><span className="h-1.5 w-1.5 rounded-full bg-slate-500" /> Inactive</>
                }
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {skill && (
            <button
              onClick={onDelete}
              className="flex h-8 w-8 items-center justify-center rounded-xl text-muted-foreground hover:text-red-400 hover:bg-red-400/10 transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            onClick={onCancel}
            className="rounded-xl px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !name.trim() || !content.trim()}
            className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-violet-500 to-violet-600 px-4 py-1.5 text-xs font-semibold text-white hover:from-violet-400 hover:to-violet-500 transition-all btn-press disabled:opacity-50"
          >
            <Save className="h-3.5 w-3.5" />
            {saving ? "Saving..." : isNew ? "Create" : "Save"}
          </button>
        </div>
      </div>

      <div className="flex-1 flex min-h-0">
        <div className="flex-[7] flex flex-col border-r border-border min-h-0">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-card/50">
            <FileText className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">Editor</span>
            <span className="ml-auto text-[10px] text-muted-foreground">{wordCount} words · {lineCount} lines</span>
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="flex-1 w-full px-4 py-3 bg-card text-[12px] text-foreground/90 font-mono leading-relaxed focus:outline-none resize-none"
            placeholder={"# Skill Name\n\n## Role\nYou are an expert...\n\n## Guidelines\n- Rule one\n- Rule two\n\n## Examples\n* Example input/output"}
            spellCheck={false}
          />
        </div>

        <div className="flex-[3] flex flex-col min-h-0">
          <div className="flex items-center border-b border-border bg-card/50">
            <button
              onClick={() => setActivePreviewTab("preview")}
              className={cn(
                "flex items-center gap-1.5 flex-1 px-3 py-2 text-[10px] font-semibold uppercase tracking-wide transition-colors border-b-2",
                activePreviewTab === "preview"
                  ? "text-violet-400 border-violet-400"
                  : "text-muted-foreground border-transparent hover:text-foreground"
              )}
            >
              <Eye className="h-3 w-3" />
              Preview
            </button>
            <button
              onClick={() => setActivePreviewTab("compliance")}
              className={cn(
                "flex items-center gap-1.5 flex-1 px-3 py-2 text-[10px] font-semibold uppercase tracking-wide transition-colors border-b-2",
                activePreviewTab === "compliance"
                  ? "text-amber-400 border-amber-400"
                  : "text-muted-foreground border-transparent hover:text-foreground"
              )}
            >
              <Sparkles className="h-3 w-3" />
              Compliance
            </button>
          </div>

          {activePreviewTab === "preview" ? (
            <div className="flex-1 overflow-y-auto px-4 py-3">
              {content.trim() ? (
                <div
                  className="space-y-0.5"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
                />
              ) : (
                <p className="text-xs text-muted-foreground/50 italic text-center py-8">Start typing to see preview</p>
              )}
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              <div className="flex items-center gap-3 p-3 rounded-xl bg-secondary/40">
                <div className="text-xl font-bold text-foreground">{complianceScore}%</div>
                <div>
                  <div className="text-[10px] font-semibold text-foreground">Compliance Score</div>
                  <div className="text-[9px] text-muted-foreground">{complianceItems.filter((i) => i.pass).length}/{complianceItems.length} rules met</div>
                </div>
                <div className={cn(
                  "ml-auto text-[10px] font-medium px-2 py-1 rounded-full",
                  complianceScore >= 80 ? "bg-emerald-500/10 text-emerald-400" :
                  complianceScore >= 50 ? "bg-amber-500/10 text-amber-400" :
                  "bg-red-500/10 text-red-400"
                )}>
                  {complianceScore >= 80 ? "Good" : complianceScore >= 50 ? "Fair" : "Needs Work"}
                </div>
              </div>

              <div className="space-y-1.5">
                {complianceItems.map((item, i) => (
                  <div key={i} className="flex items-center gap-2.5 rounded-lg p-2 bg-secondary/30">
                    {item.pass ? (
                      <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                    ) : (
                      <AlertTriangle className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
                    )}
                    <span className={cn(
                      "text-[11px] flex-1",
                      item.pass ? "text-foreground/80" : "text-muted-foreground"
                    )}>
                      {item.rule}
                    </span>
                  </div>
                ))}
              </div>

              <div className="border-t border-border pt-3">
                <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-2">Metadata</h4>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="flex-1 px-2 py-1.5 rounded-lg bg-secondary/60 border border-border text-[11px] text-foreground focus:outline-none focus:border-violet-500"
                    >
                      {Object.entries(CATEGORY_LABELS).map(([v, l]) => (
                        <option key={v} value={v}>{l}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-medium text-muted-foreground mb-1 block">Description</label>
                    <input
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Optional description..."
                      className="w-full px-2 py-1.5 rounded-lg bg-secondary/60 border border-border text-[11px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-violet-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-medium text-muted-foreground mb-1.5 block">Agent Targets</label>
                    <div className="space-y-1">
                      {AGENT_OPTIONS.map((opt) => (
                        <button
                          key={opt.id}
                          onClick={() => toggleAgent(opt.id)}
                          className={cn(
                            "flex items-center gap-2 w-full rounded-lg px-2 py-1.5 text-[11px] transition-colors",
                            agentTargets.includes(opt.id)
                              ? "bg-violet-500/10 text-violet-400"
                              : "text-muted-foreground hover:bg-secondary"
                          )}
                        >
                          {agentTargets.includes(opt.id)
                            ? <ToggleRight className="h-4 w-4 text-violet-400" />
                            : <ToggleLeft className="h-4 w-4" />
                          }
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface SkillLibraryProps {
  onSelect: (skill: Skill) => void;
  onNew: () => void;
  selectedId: string | null;
}

function SkillLibrary({ onSelect, onNew, selectedId }: SkillLibraryProps) {
  const { filterCategory, setFilterCategory } = useSkillsStore();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);

  const loadSkills = useCallback(async () => {
    setLoading(true);
    try {
      const data = await skillsApi.list(filterCategory === "all" ? undefined : filterCategory);
      setSkills(data);
    } catch {} finally {
      setLoading(false);
    }
  }, [filterCategory]);

  useEffect(() => {
    loadSkills();
  }, [loadSkills]);

  const filtered = skills.filter(
    (s) => !searchQuery || s.name.toLowerCase().includes(searchQuery.toLowerCase()) || (s.description?.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="flex flex-col h-full border-r border-border">
      <div className="px-3 py-3 border-b border-border bg-card/50">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-[11px] font-bold text-foreground uppercase tracking-wide">Skill Library</h3>
          <button
            onClick={onNew}
            className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-500/10 text-violet-400 hover:bg-violet-500/20 transition-colors"
            title="New Skill"
          >
            <Plus className="h-3.5 w-3.5" />
          </button>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-7 pr-2 py-1.5 rounded-lg bg-secondary/60 border border-border text-[11px] text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-violet-500"
          />
        </div>
        <div className="flex gap-1 mt-2 overflow-x-auto scrollbar-thin">
          {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
            <button
              key={value}
              onClick={() => setFilterCategory(value as any)}
              className={cn(
                "px-2 py-0.5 rounded text-[9px] font-medium whitespace-nowrap transition-colors",
                filterCategory === value
                  ? `${CATEGORY_BG[value]} border border-current/20`
                  : "text-muted-foreground hover:text-foreground bg-secondary/40"
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-2 space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 skeleton rounded-xl" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-[10px] text-muted-foreground">No skills found</p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {filtered.map((skill) => (
              <button
                key={skill.id}
                onClick={() => onSelect(skill)}
                className={cn(
                  "w-full text-left rounded-xl p-2.5 transition-all group",
                  selectedId === skill.id
                    ? "bg-violet-500/10 border border-violet-500/20"
                    : "hover:bg-secondary/60 border border-transparent"
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={cn("text-[10px] font-medium", CATEGORY_COLORS[skill.category] || "text-muted-foreground")}>
                    {CATEGORY_LABELS[skill.category] || skill.category}
                  </span>
                  <span className="text-[9px] text-muted-foreground ml-auto">v{skill.version}</span>
                  {!skill.active && (
                    <span className="text-[9px] text-amber-400/60">inactive</span>
                  )}
                </div>
                <div className="text-[11px] font-semibold text-foreground truncate">{skill.name}</div>
                {skill.description && (
                  <div className="text-[9px] text-muted-foreground line-clamp-1 mt-0.5">{skill.description}</div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="px-3 py-2 border-t border-border">
        <div className="text-[9px] text-muted-foreground text-center">
          {filtered.length} skill{filtered.length !== 1 ? "s" : ""}
        </div>
      </div>
    </div>
  );
}

export function SkillsStudio() {
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [isNewSkill, setIsNewSkill] = useState(false);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const showMessage = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleNew = () => {
    setSelectedSkill(null);
    setIsNewSkill(true);
  };

  const handleSelect = (skill: Skill) => {
    setSelectedSkill(skill);
    setIsNewSkill(false);
  };

  const handleCancel = () => {
    setSelectedSkill(null);
    setIsNewSkill(false);
  };

  const handleSave = async (data: { name: string; description?: string; category: string; content_markdown: string; agent_targets: string[] }) => {
    try {
      if (isNewSkill) {
        await skillsApi.create(data);
        showMessage("success", "Skill created!");
      } else if (selectedSkill) {
        await skillsApi.update(selectedSkill.id, data);
        showMessage("success", "Skill saved!");
      }
      setIsNewSkill(false);
    } catch {
      showMessage("error", "Failed to save skill");
    }
  };

  const handleDelete = async () => {
    if (!selectedSkill || !confirm("Delete this skill?")) return;
    setDeleting(true);
    try {
      await skillsApi.delete(selectedSkill.id);
      setSelectedSkill(null);
      showMessage("success", "Skill deleted!");
    } catch {
      showMessage("error", "Failed to delete skill");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="flex h-full min-h-0">
      <div className="w-64 flex-shrink-0 border-r border-border">
        <SkillLibrary
          onSelect={handleSelect}
          onNew={handleNew}
          selectedId={selectedSkill?.id ?? null}
        />
      </div>

      <div className="flex-1 min-h-0">
        {message && (
          <div className={cn(
            "absolute top-14 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl text-xs font-medium shadow-lg animate-slide-up",
            message.type === "success" ? "bg-emerald-500/90 text-white" : "bg-red-500/90 text-white"
          )}>
            {message.text}
          </div>
        )}

        <SkillEditorPanel
          skill={selectedSkill}
          isNew={isNewSkill}
          onSave={handleSave}
          onCancel={handleCancel}
          onDelete={selectedSkill ? handleDelete : undefined}
        />
      </div>
    </div>
  );
}