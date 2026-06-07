"use client";

import { useEffect, useState } from "react";
import {
  Activity, Brain, Clock, Database, FileOutput,
  FolderOpen, Layers, Plus, Projector, Search, Settings,
  Sparkles, TrendingUp, Workflow
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useProjectStore } from "@/store/project-store";
import { projectApi, type Project, type ProjectDashboard, type ProjectSummary } from "@/lib/projects-api";
import type { SectionName } from "@/types/api";
import { useUIStore } from "@/store/ui-store";

type Tab = "overview" | "memories" | "skills" | "sources" | "pipelines" | "outputs" | "analytics" | "settings";

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "overview", label: "Overview", icon: Activity },
  { id: "memories", label: "Memories", icon: Brain },
  { id: "skills", label: "Skills", icon: Sparkles },
  { id: "sources", label: "Sources", icon: Database },
  { id: "pipelines", label: "Pipelines", icon: Workflow },
  { id: "outputs", label: "Outputs", icon: FileOutput },
  { id: "analytics", label: "Analytics", icon: TrendingUp },
  { id: "settings", label: "Settings", icon: Settings },
];

function ProjectCard({ project, onSelect }: { project: ProjectSummary; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className="w-full text-left group relative overflow-hidden rounded-2xl border border-border bg-card/60 backdrop-blur-xl p-4 transition-all duration-300 hover:bg-card/80 hover:border-border-light hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-violet-500/0 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      <div className="relative">
        <div className="flex items-start justify-between mb-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/20 to-violet-600/10 text-sm font-bold text-violet-400 shrink-0">
            {project.name.charAt(0).toUpperCase()}
          </div>
          {project.archived && (
            <span className="text-[10px] font-medium text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded-full">
              Archived
            </span>
          )}
        </div>
        <div className="text-sm font-semibold text-foreground mb-1 truncate">{project.name}</div>
        {project.description && (
          <div className="text-[11px] text-muted-foreground line-clamp-2 mb-3">{project.description}</div>
        )}
        <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Brain className="h-3 w-3" />
            {project.total_memories}
          </span>
          <span className="flex items-center gap-1">
            <FileOutput className="h-3 w-3" />
            {project.total_outputs}
          </span>
          {project.last_activity && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {new Date(project.last_activity).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

interface ProjectWorkspaceHeaderProps {
  project: Project | null;
  dashboard: ProjectDashboard | null;
  loading: boolean;
  onStatClick?: (tab: Tab) => void;
}

function ProjectWorkspaceHeader({ project, dashboard, loading, onStatClick }: ProjectWorkspaceHeaderProps) {
  const setSection = useUIStore((s) => s.setSection);
  const openModal = useUIStore((s) => s.openModal);
  const selectProject = useProjectStore((s) => s.selectProject);
  const projectName = project?.title || project?.topic || "";

  const handleCreatePipeline = () => openModal("pipeline-create");

  const handleBack = () => {
    selectProject(null);
  };

  const handleStatClick = (tab: Tab) => {
    onStatClick?.(tab);
  };

  if (!project && !loading) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-xl p-5">
      {loading ? (
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 skeleton rounded-2xl" />
          <div className="flex-1 space-y-2">
            <div className="h-5 w-40 skeleton rounded" />
            <div className="h-3 w-64 skeleton rounded" />
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/20 to-violet-600/10 text-lg font-bold text-violet-400 shadow-lg shadow-violet-500/10 shrink-0">
            {projectName.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-bold text-foreground">{projectName}</h2>
              <span className="status-dot success" />
            </div>
            {project?.topic && (
              <p className="text-xs text-muted-foreground mb-3">{project.topic}</p>
            )}
            <div className="flex flex-wrap items-center gap-3">
              <button onClick={() => handleStatClick("memories")} className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                <Brain className="h-3.5 w-3.5 text-violet-400" />
                <span className="font-medium text-foreground">{dashboard?.total_memories ?? 0}</span> memories
              </button>
              <button onClick={() => handleStatClick("outputs")} className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                <FileOutput className="h-3.5 w-3.5 text-emerald-400" />
                <span className="font-medium text-foreground">{dashboard?.total_outputs ?? 0}</span> outputs
              </button>
              <button onClick={() => handleStatClick("sources")} className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                <Database className="h-3.5 w-3.5 text-blue-400" />
                <span className="font-medium text-foreground">{dashboard?.total_sources ?? 0}</span> sources
              </button>
              <button onClick={() => handleStatClick("analytics")} className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                <Layers className="h-3.5 w-3.5 text-amber-400" />
                <span className="font-medium text-foreground">{dashboard?.total_tokens_used?.toLocaleString() ?? 0}</span> tokens
              </button>
              {dashboard?.last_activity && (
                <button onClick={() => handleStatClick("analytics")} className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
                  <Clock className="h-3.5 w-3.5 text-muted-foreground/60" />
                  <span>Last activity {new Date(dashboard.last_activity).toLocaleDateString()}</span>
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleCreatePipeline}
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-violet-500 to-violet-600 px-3 py-2 text-xs font-semibold text-white hover:from-violet-400 hover:to-violet-500 transition-all btn-press shadow-lg shadow-violet-500/20"
            >
              <Plus className="h-3.5 w-3.5" />
              New Pipeline
            </button>
            <button
              onClick={handleBack}
              className="flex items-center gap-1.5 rounded-xl bg-secondary/60 px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-secondary transition-colors"
            >
              <FolderOpen className="h-3.5 w-3.5" />
              All Projects
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

interface ProjectOverviewTabProps {
  dashboard: ProjectDashboard | null;
  loading: boolean;
  setActiveTab: (tab: Tab) => void;
}

function ProjectOverviewTab({ dashboard, loading, setActiveTab }: ProjectOverviewTabProps) {
  const stats = dashboard ? [
    { label: "Total Outputs", value: dashboard.total_outputs, icon: FileOutput, accent: "emerald", tab: "outputs" as Tab },
    { label: "Total Memories", value: dashboard.total_memories, icon: Brain, accent: "blue", tab: "memories" as Tab },
    { label: "Total Sources", value: dashboard.total_sources, icon: Database, accent: "violet", tab: "sources" as Tab },
    { label: "Tokens Used", value: dashboard.total_tokens_used.toLocaleString(), icon: Layers, accent: "amber", tab: "analytics" as Tab },
    { label: "Est. Cost", value: `$${dashboard.total_cost.toFixed(2)}`, icon: Activity, accent: "emerald", tab: "analytics" as Tab },
    { label: "Last Activity", value: dashboard.last_activity ? new Date(dashboard.last_activity).toLocaleDateString() : "N/A", icon: Clock, accent: "muted", tab: "analytics" as Tab },
  ] : [];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-3 xl:grid-cols-6">
        {stats.map((s) => (
          <button
            key={s.label}
            onClick={() => setActiveTab(s.tab)}
            className="rounded-2xl border border-border bg-card/40 p-3 text-left hover:bg-card/60 hover:border-border-light transition-all cursor-pointer group"
          >
            <div className={cn(
              "flex h-8 w-8 items-center justify-center rounded-xl mb-2",
              s.accent === "emerald" && "bg-emerald-500/10 text-emerald-400",
              s.accent === "blue" && "bg-blue-500/10 text-blue-400",
              s.accent === "violet" && "bg-violet-500/10 text-violet-400",
              s.accent === "amber" && "bg-amber-500/10 text-amber-400",
              s.accent === "muted" && "bg-secondary text-muted-foreground",
            )}>
              <s.icon className="h-4 w-4" />
            </div>
            <div className="text-lg font-bold text-foreground">{loading ? "—" : s.value}</div>
            <div className="text-[10px] text-muted-foreground group-hover:text-foreground transition-colors">{s.label}</div>
          </button>
        ))}
      </div>
      {dashboard?.recent_workflows && dashboard.recent_workflows.length > 0 && (
        <div className="rounded-2xl border border-border bg-card/40 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground">Recent Pipelines</h3>
            <button
              onClick={() => setActiveTab("pipelines")}
              className="text-[10px] text-violet-400 hover:text-violet-300 font-medium transition-colors cursor-pointer"
            >
              View all
            </button>
          </div>
          <div className="space-y-2">
            {(dashboard.recent_workflows as any[]).slice(0, 5).map((w: any, i: number) => (
              <button
                key={i}
                onClick={() => setActiveTab("pipelines")}
                className="w-full flex items-center justify-between rounded-xl bg-secondary/40 p-2.5 hover:bg-secondary/60 transition-colors cursor-pointer text-left"
              >
                <div className="flex items-center gap-2">
                  <Projector className="h-3.5 w-3.5 text-violet-400" />
                  <span className="text-xs font-medium text-foreground truncate max-w-[200px]">{w.topic || "Untitled"}</span>
                </div>
                <span className="text-[10px] text-muted-foreground flex-shrink-0">
                  {new Date(w.created_at).toLocaleDateString()}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface ProjectPipelinesTabProps {
  projectId: string;
}

function ProjectPipelinesTab({ projectId }: ProjectPipelinesTabProps) {
  const pipelines = useProjectStore((s) => s.projects);
  const setSection = useUIStore((s) => s.setSection);

  const handleRunPipeline = (id: string) => {
    setSection("pipeline");
  };

  return (
    <div className="rounded-2xl border border-border bg-card/40 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground">Pipelines</h3>
        <button
          onClick={() => setSection("pipeline")}
          className="flex items-center gap-1.5 text-xs text-violet-400 hover:text-violet-300 font-medium transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          New Pipeline
        </button>
      </div>
      <div className="space-y-2">
        {pipelines.filter((p) => !("workflow_id" in p)).length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-6">No pipelines in this project yet</p>
        ) : (
          pipelines.filter((p) => !("workflow_id" in p)).slice(0, 10).map((p: any) => (
            <button
              key={p.id}
              onClick={() => handleRunPipeline(p.id)}
              className="w-full flex items-center justify-between rounded-xl bg-secondary/40 p-2.5 hover:bg-secondary/60 transition-colors cursor-pointer text-left"
            >
              <div className="flex items-center gap-2">
                <span className={cn("status-dot", p.archived ? "skipped" : "success")} />
                <span className="text-xs font-medium text-foreground truncate max-w-[200px]">{p.name}</span>
              </div>
              <span className="text-[10px] text-muted-foreground">{new Date(p.created_at).toLocaleDateString()}</span>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

interface ProjectOutputsTabProps {
  projectId: string;
}

function ProjectOutputsTab({ projectId }: ProjectOutputsTabProps) {
  const [outputs, setOutputs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projectApi.getOutputs(projectId).then((data) => {
      setOutputs(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [projectId]);

  return (
    <div className="rounded-2xl border border-border bg-card/40 p-4">
      <h3 className="text-sm font-semibold text-foreground mb-4">Outputs</h3>
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 skeleton rounded-xl" />
          ))}
        </div>
      ) : outputs.length === 0 ? (
        <p className="text-xs text-muted-foreground text-center py-6">No outputs yet</p>
      ) : (
        <div className="space-y-2">
          {outputs.slice(0, 10).map((o) => (
            <button
              key={o.id}
              onClick={() => {/* future: open output detail */}}
              className="w-full flex items-center gap-2.5 rounded-xl bg-secondary/40 p-2.5 hover:bg-secondary/60 transition-colors cursor-pointer text-left"
            >
              <FileOutput className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-foreground truncate">{o.title || "Untitled"}</div>
                <div className="text-[10px] text-muted-foreground">{o.content_type}</div>
              </div>
              <span className="text-[10px] text-muted-foreground flex-shrink-0">{new Date(o.created_at).toLocaleDateString()}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

interface ProjectSettingsTabProps {
  project: ProjectSummary | null;
  projectId: string;
}

function ProjectSettingsTab({ project, projectId }: ProjectSettingsTabProps) {
  const [name, setName] = useState(project?.name || "");
  const [description, setDescription] = useState(project?.description || "");
  const [archived, setArchived] = useState(project?.archived || false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const updateProject = useProjectStore((s) => s.updateProject);

  useEffect(() => {
    if (project) {
      setName(project.name);
      setDescription(project.description || "");
      setArchived(project.archived);
    }
  }, [project]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateProject(projectId, { name, description, archived });
      setMessage("Saved!");
      setTimeout(() => setMessage(""), 2000);
    } catch {
      setMessage("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-card/40 p-4 space-y-4 max-w-lg">
      <h3 className="text-sm font-semibold text-foreground">Project Settings</h3>
      <div className="space-y-3">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1 block">Name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-secondary/60 border border-border text-sm text-foreground focus:outline-none focus:border-violet-500 input-glow"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1 block">Description</label>
          <textarea
            value={description || ""}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 rounded-xl bg-secondary/60 border border-border text-sm text-foreground focus:outline-none focus:border-violet-500 input-glow resize-none"
          />
        </div>
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="archived"
            checked={archived}
            onChange={(e) => setArchived(e.target.checked)}
            className="rounded"
          />
          <label htmlFor="archived" className="text-xs font-medium text-muted-foreground">Archived</label>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-xl bg-gradient-to-r from-violet-500 to-violet-600 px-4 py-2 text-xs font-semibold text-white hover:from-violet-400 hover:to-violet-500 transition-all btn-press disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
          {message && <span className="text-xs text-muted-foreground">{message}</span>}
        </div>
      </div>
    </div>
  );
}

export function ProjectsSection() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const { currentProject, currentProjectId, projects, loading: projectsLoading, loadProjects, selectProject } = useProjectStore();
  const [dashboard, setDashboard] = useState<ProjectDashboard | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [creating, setCreating] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const createProject = useProjectStore((s) => s.createProject);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    if (currentProjectId) {
      setDashboardLoading(true);
      projectApi.getDashboard(currentProjectId).then(setDashboard).finally(() => setDashboardLoading(false)).catch(() => setDashboardLoading(false));
    } else {
      setDashboard(null);
    }
  }, [currentProjectId]);

  const handleSelectProject = async (id: string) => {
    await selectProject(id);
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    setCreating(true);
    try {
      await createProject(newProjectName.trim());
      setNewProjectName("");
    } catch {}
    setCreating(false);
  };

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const showProjectWorkspace = currentProjectId && currentProject;

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-foreground">Projects</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {showProjectWorkspace ? (currentProject?.title || currentProject?.topic) : `${projects.length} workspace${projects.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        {!showProjectWorkspace && (
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-2 rounded-xl bg-secondary/60 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-violet-500 w-full min-w-[120px] max-w-xs"
              />
            </div>
            <div className="flex items-center gap-1.5 rounded-xl bg-secondary/60 border border-border px-2 py-1.5">
              <input
                type="text"
                placeholder="New project..."
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreateProject()}
                className="bg-transparent text-xs text-foreground placeholder:text-muted-foreground w-24 min-w-[80px] focus:outline-none"
              />
              <button
                onClick={handleCreateProject}
                disabled={creating || !newProjectName.trim()}
                className="flex items-center gap-1 rounded-lg bg-violet-500/20 px-2 py-1 text-xs font-medium text-violet-400 hover:bg-violet-500/30 disabled:opacity-50 transition-colors"
              >
                <Plus className="h-3 w-3" />
                Create
              </button>
            </div>
          </div>
        )}
      </div>

      {showProjectWorkspace ? (
        <div className="flex-1 overflow-y-auto space-y-4 min-h-0">
          <ProjectWorkspaceHeader
            project={currentProject as any}
            dashboard={dashboard}
            loading={dashboardLoading}
            onStatClick={setActiveTab}
          />

          <div className="border-b border-border">
            <nav className="flex gap-1 overflow-x-auto scrollbar-thin">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors",
                    activeTab === tab.id
                      ? "text-violet-400 border-violet-400"
                      : "text-muted-foreground border-transparent hover:text-foreground hover:border-border"
                  )}
                >
                  <tab.icon className="h-3.5 w-3.5" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="flex-1 overflow-y-auto">
            {activeTab === "overview" && <ProjectOverviewTab dashboard={dashboard} loading={dashboardLoading} setActiveTab={setActiveTab} />}
            {activeTab === "memories" && currentProjectId && (
              <div className="rounded-2xl border border-border bg-card/40 p-4">
                <h3 className="text-sm font-semibold text-foreground mb-4">Memories</h3>
                <p className="text-xs text-muted-foreground">Memory management coming soon...</p>
              </div>
            )}
            {activeTab === "skills" && (
              <div className="rounded-2xl border border-border bg-card/40 p-4">
                <h3 className="text-sm font-semibold text-foreground mb-4">Skills</h3>
                <p className="text-xs text-muted-foreground">Project skills management coming soon...</p>
              </div>
            )}
            {activeTab === "sources" && (
              <div className="rounded-2xl border border-border bg-card/40 p-4">
                <h3 className="text-sm font-semibold text-foreground mb-4">Sources</h3>
                <p className="text-xs text-muted-foreground">Source governance coming soon...</p>
              </div>
            )}
            {activeTab === "pipelines" && currentProjectId && <ProjectPipelinesTab projectId={currentProjectId} />}
            {activeTab === "outputs" && currentProjectId && <ProjectOutputsTab projectId={currentProjectId} />}
            {activeTab === "analytics" && (
              <div className="rounded-2xl border border-border bg-card/40 p-4">
                <h3 className="text-sm font-semibold text-foreground mb-4">Analytics</h3>
                <p className="text-xs text-muted-foreground">Project analytics coming soon...</p>
              </div>
            )}
            {activeTab === "settings" && currentProject && (
              <ProjectSettingsTab project={currentProject as any} projectId={currentProjectId!} />
            )}
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          {projectsLoading ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-36 skeleton rounded-2xl" />
              ))}
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <FolderOpen className="h-12 w-12 text-muted-foreground/20 mb-4" />
              <h3 className="text-sm font-semibold text-foreground mb-1">No projects yet</h3>
              <p className="text-xs text-muted-foreground mb-4">Create your first project to get started</p>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Project name..."
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreateProject()}
                  className="px-3 py-2 rounded-xl bg-secondary/60 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-violet-500 w-full min-w-[120px] max-w-xs"
                />
                <button
                  onClick={handleCreateProject}
                  disabled={creating || !newProjectName.trim()}
                  className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-violet-500 to-violet-600 px-4 py-2 text-xs font-semibold text-white hover:from-violet-400 hover:to-violet-500 transition-all btn-press disabled:opacity-50"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Create
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {filteredProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onSelect={() => handleSelectProject(project.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}