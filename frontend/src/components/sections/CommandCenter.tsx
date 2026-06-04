"use client";

import { useEffect, useState } from "react";
import { Activity, BookOpen, Brain, ChevronRight, FileOutput, FolderOpen, Layers, Play, Plus, Projector, RefreshCw, Sparkles, TrendingUp, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui-store";
import { usePipelineStore } from "@/store/pipeline-store";
import { useProjectStore } from "@/store/project-store";
import { useProvidersStats } from "@/hooks/use-providers-stats";
import type { ProvidersStatsResponse } from "@/types/api";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: string;
  accent?: string;
  loading?: boolean;
}

function StatCard({ label, value, icon, trend, accent = "violet", loading }: StatCardProps) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border bg-card/60 backdrop-blur-xl p-4 transition-all duration-300 hover:bg-card/80 hover:border-border-light hover:-translate-y-0.5 hover:shadow-lg cursor-pointer">
      <div className={cn(
        "absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500",
        accent === "violet" && "bg-gradient-to-br from-violet-500/5 to-transparent",
        accent === "emerald" && "bg-gradient-to-br from-emerald-500/5 to-transparent",
        accent === "blue" && "bg-gradient-to-br from-blue-500/5 to-transparent",
        accent === "amber" && "bg-gradient-to-br from-amber-500/5 to-transparent",
      )} />
      <div className="relative">
        <div className="flex items-center justify-between mb-3">
          <div className={cn(
            "flex h-9 w-9 items-center justify-center rounded-xl",
            accent === "violet" && "bg-violet-500/10 text-violet-400",
            accent === "emerald" && "bg-emerald-500/10 text-emerald-400",
            accent === "blue" && "bg-blue-500/10 text-blue-400",
            accent === "amber" && "bg-amber-500/10 text-amber-400",
          )}>
            {icon}
          </div>
          {trend && (
            <span className="text-[10px] font-medium text-emerald-400 flex items-center gap-0.5">
              <TrendingUp className="h-3 w-3" />
              {trend}
            </span>
          )}
        </div>
        {loading ? (
          <div className="space-y-2">
            <div className="h-7 w-16 skeleton rounded" />
            <div className="h-3 w-20 skeleton rounded" />
          </div>
        ) : (
          <>
            <div className="text-2xl font-bold text-foreground mb-0.5">{value}</div>
            <div className="text-xs text-muted-foreground font-medium">{label}</div>
          </>
        )}
      </div>
    </div>
  );
}

interface ProviderHealthMiniProps {
  stats: ProvidersStatsResponse | null;
  loading: boolean;
}

function ProviderHealthMini({ stats, loading }: ProviderHealthMiniProps) {
  const providers = stats ? Object.values(stats) : [];
  const getHealthColor = (state: string, successRate: number) => {
    if (state === "circuit_open" || state === "open") return "bg-red-400";
    if (successRate < 0.8) return "bg-amber-400";
    return "bg-emerald-400";
  };

  return (
    <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground">Provider Health</h3>
        {loading && <RefreshCw className="h-3 w-3 animate-spin text-muted-foreground" />}
      </div>
      {loading && !stats ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="h-8 w-8 skeleton rounded-lg" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3 w-16 skeleton rounded" />
                <div className="h-2 w-24 skeleton rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {providers.map((p) => (
            <div key={p.provider} className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary/60">
                <span className={cn("status-dot", getHealthColor(p.circuit_state, p.success_rate))} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-foreground capitalize">{p.provider}</div>
                <div className="text-[10px] text-muted-foreground">
                  {p.success_rate.toFixed(0)}% · {p.average_latency.toFixed(0)}ms · {p.rpm_used}/{p.rpm_limit} RPM
                </div>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50" />
            </div>
          ))}
          {providers.length === 0 && (
            <p className="text-xs text-muted-foreground text-center py-4">No providers configured</p>
          )}
        </div>
      )}
      <button
        onClick={() => useUIStore.getState().setSection("operations")}
        className="mt-3 w-full text-xs text-violet-400 hover:text-violet-300 font-medium transition-colors"
      >
        View all operations →
      </button>
    </div>
  );
}

interface ActivePipelinesMiniProps {
  onViewPipeline: (id: string) => void;
}

function ActivePipelinesMini({ onViewPipeline }: ActivePipelinesMiniProps) {
  const pipelines = usePipelineStore((s) => s.pipelines);
  const running = pipelines.filter((p) => p.status === "running" || p.status === "pending");

  return (
    <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Play className="h-3.5 w-3.5 text-blue-400" />
          Active Pipelines
        </h3>
        <span className="text-[10px] font-medium text-muted-foreground">{running.length} running</span>
      </div>
      {running.length === 0 ? (
        <div className="text-center py-6">
          <Activity className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
          <p className="text-xs text-muted-foreground">No active pipelines</p>
        </div>
      ) : (
        <div className="space-y-2">
          {running.slice(0, 4).map((p) => (
            <button
              key={p.workflow_id}
              onClick={() => onViewPipeline(p.workflow_id)}
              className="w-full flex items-center gap-2.5 rounded-xl bg-secondary/40 p-2.5 text-left hover:bg-secondary/60 transition-colors"
            >
              <span className="status-dot running flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-foreground truncate">{p.topic}</div>
                <div className="text-[10px] text-muted-foreground capitalize">{p.status}</div>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50 flex-shrink-0" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

interface ActivityTimelineMiniProps {
  events: { action: string; node?: string; timestamp: string; status?: string; details?: string }[];
}

function ActivityTimelineMini({ events }: ActivityTimelineMiniProps) {
  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch { return "--:--"; }
  };

  const recentEvents = events.slice(-12).reverse();

  return (
    <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Zap className="h-3.5 w-3.5 text-amber-400" />
          Recent Activity
        </h3>
      </div>
      {recentEvents.length === 0 ? (
        <div className="text-center py-6">
          <Activity className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
          <p className="text-xs text-muted-foreground">No recent activity</p>
        </div>
      ) : (
        <div className="space-y-1 max-h-[280px] overflow-y-auto scrollbar-thin">
          {recentEvents.map((e, i) => (
            <div key={i} className="flex items-start gap-2.5 py-1.5 border-b border-border/40 last:border-0">
              <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-violet-400/60 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-medium text-foreground leading-snug">{e.action}</div>
                {e.node && <div className="text-[10px] text-muted-foreground capitalize">{e.node}</div>}
              </div>
              <span className="text-[10px] text-muted-foreground flex-shrink-0 font-mono">
                {formatTime(e.timestamp)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface LatestOutputsMiniProps {
  onCreatePipeline: () => void;
}

function LatestOutputsMini({ onCreatePipeline }: LatestOutputsMiniProps) {
  const pipelines = usePipelineStore((s) => s.pipelines);
  const completed = pipelines.filter((p) => p.status === "completed").slice(0, 5);

  return (
    <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <FileOutput className="h-3.5 w-3.5 text-emerald-400" />
          Latest Outputs
        </h3>
      </div>
      {completed.length === 0 ? (
        <div className="text-center py-6">
          <FileOutput className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
          <p className="text-xs text-muted-foreground mb-3">No outputs yet</p>
          <button
            onClick={onCreatePipeline}
            className="text-xs text-violet-400 hover:text-violet-300 font-medium transition-colors"
          >
            Create your first pipeline →
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {completed.map((p) => (
            <div key={p.workflow_id} className="flex items-center gap-2.5 rounded-xl bg-secondary/40 p-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 flex-shrink-0">
                <FileOutput className="h-3.5 w-3.5 text-emerald-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-foreground truncate">{p.topic}</div>
                <div className="text-[10px] text-muted-foreground">
                  {p.total_tokens ? `${p.total_tokens.toLocaleString()} tokens` : "Completed"}
                </div>
              </div>
              <span className="status-dot success flex-shrink-0" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface QuickStartProps {
  onCreatePipeline: () => void;
  onViewProjects: () => void;
}

function QuickStart({ onCreatePipeline, onViewProjects }: QuickStartProps) {
  return (
    <div className="rounded-2xl border border-border bg-gradient-to-br from-violet-500/5 via-card/60 to-card/60 backdrop-blur-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="h-4 w-4 text-violet-400" />
        <h3 className="text-sm font-semibold text-foreground">Quick Start</h3>
      </div>
      <div className="space-y-2">
        <button
          onClick={onCreatePipeline}
          className="w-full flex items-center gap-3 rounded-xl bg-gradient-to-r from-violet-500/10 to-violet-600/5 p-3 hover:from-violet-500/20 hover:to-violet-600/10 transition-all group"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-violet-500/20 group-hover:bg-violet-500/30 transition-colors">
            <Plus className="h-4 w-4 text-violet-400" />
          </div>
          <div className="text-left">
            <div className="text-xs font-semibold text-foreground">New Pipeline</div>
            <div className="text-[10px] text-muted-foreground">Generate AI content</div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50 ml-auto" />
        </button>
        <button
          onClick={onViewProjects}
          className="w-full flex items-center gap-3 rounded-xl bg-secondary/40 p-3 hover:bg-secondary/60 transition-all group"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/10 group-hover:bg-blue-500/20 transition-colors">
            <FolderOpen className="h-4 w-4 text-blue-400" />
          </div>
          <div className="text-left">
            <div className="text-xs font-semibold text-foreground">Browse Projects</div>
            <div className="text-[10px] text-muted-foreground">Manage workspaces</div>
          </div>
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50 ml-auto" />
        </button>
      </div>
    </div>
  );
}

export function CommandCenter() {
  const { stats, loading: statsLoading } = useProvidersStats();
  const events = usePipelineStore((s) => s.events);
  const pipelines = usePipelineStore((s) => s.pipelines);
  const projectCount = useProjectStore((s) => s.projects.length);
  const [projectsLoaded, setProjectsLoaded] = useState(false);

  useEffect(() => {
    useProjectStore.getState().loadProjects().then(() => setProjectsLoaded(true));
  }, []);

  const setSection = useUIStore((s) => s.setSection);
  const create = usePipelineStore((s) => s.create);
  const run = usePipelineStore((s) => s.run);

  const handleCreatePipeline = async () => {
    try {
      const id = await create("AI Research on Emerging Technologies", "technical", "professional");
      await run(id);
      setSection("pipeline");
    } catch {}
  };

  const handleViewPipeline = (id: string) => {
    usePipelineStore.getState().select(id);
    setSection("pipeline");
  };

  const handleViewProjects = () => {
    setSection("projects");
  };

  const runningCount = pipelines.filter((p) => p.status === "running" || p.status === "pending").length;
  const completedCount = pipelines.filter((p) => p.status === "completed").length;
  const totalTokens = pipelines.reduce((sum, p) => sum + (p.total_tokens || 0), 0);

  const getActionLabel = (event: { type: string; node?: string; status?: string }) => {
    switch (event.type) {
      case "connected": return "Pipeline connected";
      case "node_completed": return `${event.node} completed`;
      case "pipeline_completed": return "Pipeline completed";
      case "pipeline_failed": return "Pipeline failed";
      case "node_started": return `${event.node} started`;
      default: return event.type;
    }
  };

  const sseEvents = events.map((e) => ({
    action: getActionLabel(e as any),
    node: e.node,
    timestamp: new Date().toISOString(),
    status: e.status,
  }));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Command Center</h1>
          <p className="text-xs text-muted-foreground mt-0.5">AI Content Intelligence Platform overview</p>
        </div>
        <button
          onClick={handleCreatePipeline}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-violet-600 px-4 py-2 text-xs font-semibold text-white hover:from-violet-400 hover:to-violet-500 transition-all btn-press shadow-lg shadow-violet-500/20"
        >
          <Plus className="h-3.5 w-3.5" />
          New Pipeline
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
        <StatCard
          label="Projects"
          value={projectCount}
          icon={<FolderOpen className="h-4 w-4" />}
          accent="violet"
          loading={!projectsLoaded}
        />
        <StatCard
          label="Running"
          value={runningCount}
          icon={<Play className="h-4 w-4" />}
          accent="blue"
        />
        <StatCard
          label="Completed"
          value={completedCount}
          icon={<Layers className="h-4 w-4" />}
          accent="emerald"
        />
        <StatCard
          label="Memories"
          value="—"
          icon={<Brain className="h-4 w-4" />}
          accent="violet"
        />
        <StatCard
          label="Skills"
          value="—"
          icon={<Sparkles className="h-4 w-4" />}
          accent="amber"
        />
        <StatCard
          label="Outputs"
          value={completedCount}
          icon={<BookOpen className="h-4 w-4" />}
          accent="emerald"
        />
        <StatCard
          label="Token Usage"
          value={totalTokens > 0 ? `${(totalTokens / 1000).toFixed(1)}K` : "—"}
          icon={<TrendingUp className="h-4 w-4" />}
          accent="blue"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <ActivityTimelineMini events={sseEvents} />
          <LatestOutputsMini onCreatePipeline={handleCreatePipeline} />
        </div>
        <div className="space-y-4">
          <ProviderHealthMini stats={stats} loading={statsLoading} />
          <ActivePipelinesMini onViewPipeline={handleViewPipeline} />
          <QuickStart onCreatePipeline={handleCreatePipeline} onViewProjects={handleViewProjects} />
        </div>
      </div>
    </div>
  );
}