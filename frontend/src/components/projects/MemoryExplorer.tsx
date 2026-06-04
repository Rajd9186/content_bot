"use client";

import { useEffect, useState, useCallback, memo } from "react";
import {
  Brain, ChevronRight, Clock, Database, ExternalLink,
  FileOutput, Filter, Hash, MessageSquare, Mic2,
  Pin, PinOff, Plus, RefreshCw, Search, Tag, Trash2, TrendingUp,
  Lightbulb, CheckCircle2, AlertCircle, ArrowUpDown
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useProjectStore } from "@/store/project-store";
import { projectApi, type Memory } from "@/lib/projects-api";

type Tab = "prompts" | "outputs" | "research" | "facts" | "decisions" | "pinned";
type SortField = "date" | "confidence" | "type";
type SortDir = "asc" | "desc";

const TAB_CONFIG: { id: Tab; label: string; icon: React.ElementType; color: string }[] = [
  { id: "prompts", label: "Prompts", icon: MessageSquare, color: "text-blue-400" },
  { id: "outputs", label: "Outputs", icon: FileOutput, color: "text-emerald-400" },
  { id: "research", label: "Research", icon: Database, color: "text-violet-400" },
  { id: "facts", label: "Facts", icon: CheckCircle2, color: "text-red-400" },
  { id: "decisions", label: "Decisions", icon: Lightbulb, color: "text-amber-400" },
  { id: "pinned", label: "Pinned", icon: Pin, color: "text-yellow-400" },
];

const TYPE_STYLES: Record<string, { border: string; bg: string; icon: React.ElementType; label: string; color: string }> = {
  prompt: { border: "border-blue-500/30", bg: "bg-blue-500/5", icon: MessageSquare, label: "Prompt", color: "text-blue-400" },
  output: { border: "border-emerald-500/30", bg: "bg-emerald-500/5", icon: FileOutput, label: "Output", color: "text-emerald-400" },
  research: { border: "border-violet-500/30", bg: "bg-violet-500/5", icon: Database, label: "Research", color: "text-violet-400" },
  fact: { border: "border-red-500/30", bg: "bg-red-500/5", icon: AlertCircle, label: "Fact", color: "text-red-400" },
  user_preference: { border: "border-amber-500/30", bg: "bg-amber-500/5", icon: Hash, label: "Preference", color: "text-amber-400" },
  decision: { border: "border-orange-500/30", bg: "bg-orange-500/5", icon: Lightbulb, label: "Decision", color: "text-orange-400" },
  summary: { border: "border-border", bg: "bg-secondary/30", icon: TrendingUp, label: "Summary", color: "text-muted-foreground" },
};

interface MemoryCardProps {
  memory: Memory;
  onPin: (id: string) => void;
  onDelete: (id: string) => void;
  onClick?: (memory: Memory) => void;
  showPin?: boolean;
}

interface MemoryDetailModalProps {
  memory: Memory;
  onClose: () => void;
  onPin: (id: string) => void;
  onDelete: (id: string) => void;
}

const MemoryCard = memo(function MemoryCard({ memory, onPin, onDelete, onClick, showPin = true }: MemoryCardProps) {
  const style = TYPE_STYLES[memory.memory_type] || TYPE_STYLES.summary;
  const Icon = style.icon;

  const formatDate = (ts: string) => {
    try {
      return new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    } catch { return "—"; }
  };

  const confidencePct = (memory.confidence_score * 100).toFixed(0);

  return (
    <div
      className={cn(
        "rounded-2xl border p-4 transition-all duration-200 hover:bg-card/60 group",
        style.border, style.bg
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl",
          "bg-secondary/60 group-hover:bg-secondary transition-colors"
        )}>
          <Icon className={cn("h-4 w-4", style.color)} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              {style.label}
            </span>
            {memory.pinned && (
              <span className="flex items-center gap-0.5 text-[9px] font-medium text-yellow-400 bg-yellow-400/10 px-1.5 py-0.5 rounded-full">
                <Pin className="h-2.5 w-2.5" />
                Pinned
              </span>
            )}
            <span className="ml-auto text-[9px] text-muted-foreground font-mono">
              {formatDate(memory.created_at)}
            </span>
          </div>

          <p
            onClick={() => onClick?.(memory)}
            className={cn(
              "text-[13px] text-foreground/90 leading-relaxed line-clamp-3 cursor-pointer hover:text-foreground transition-colors",
              onClick && "cursor-pointer"
            )}
          >
            {memory.content}
          </p>

          <div className="flex items-center gap-3 mt-2">
            <div className="flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-muted-foreground/60" />
              <span className="text-[10px] text-muted-foreground">
                {confidencePct}% confidence
              </span>
            </div>
            {memory.priority !== 0 && (
              <div className="flex items-center gap-1">
                <Tag className="h-3 w-3 text-muted-foreground/60" />
                <span className="text-[10px] text-muted-foreground">priority {memory.priority}</span>
              </div>
            )}
          </div>
        </div>

        {showPin && (
          <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
            <button
              onClick={() => onPin(memory.id)}
              className="flex h-7 w-7 items-center justify-center rounded-lg hover:bg-yellow-500/10 transition-colors"
              title={memory.pinned ? "Unpin" : "Pin"}
            >
              {memory.pinned
                ? <PinOff className="h-3 w-3 text-yellow-400" />
                : <Pin className="h-3 w-3 text-muted-foreground hover:text-yellow-400" />
              }
            </button>
            <button
              onClick={() => onDelete(memory.id)}
              className="flex h-7 w-7 items-center justify-center rounded-lg hover:bg-red-500/10 transition-colors"
              title="Delete"
            >
              <Trash2 className="h-3 w-3 text-muted-foreground hover:text-red-400" />
            </button>
          </div>
        )}
      </div>
    </div>
);
});

const MemoryDetailModal = memo(function MemoryDetailModal({ memory, onClose, onPin, onDelete }: MemoryDetailModalProps) {
  const style = TYPE_STYLES[memory.memory_type] || TYPE_STYLES.summary;
  const Icon = style.icon;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="memory-detail-title"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-card/95 backdrop-blur-xl rounded-2xl border border-border w-full max-w-2xl max-h-[80vh] overflow-hidden shadow-2xl animate-bounce-in mx-4"
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-3">
            <div className={cn("flex h-9 w-9 items-center justify-center rounded-xl bg-secondary/60")}>
              <Icon className={cn("h-4 w-4", style.color)} />
            </div>
            <div>
              <h2 id="memory-detail-title" className="text-sm font-bold text-foreground">{style.label}</h2>
              <p className="text-[10px] text-muted-foreground">Memory Detail</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => { onPin(memory.id); onClose(); }}
              className="flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-yellow-400 hover:bg-yellow-400/10 transition-colors"
            >
              {memory.pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
              {memory.pinned ? "Unpin" : "Pin"}
            </button>
            <button
              onClick={() => { onDelete(memory.id); onClose(); }}
              className="flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-red-400 hover:bg-red-400/10 transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete
            </button>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-xl hover:bg-secondary transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="overflow-y-auto p-5 space-y-4 max-h-[calc(80vh-80px)]">
          <div className="rounded-2xl bg-secondary/30 border border-border p-4">
            <pre className="text-[13px] text-foreground/90 leading-relaxed whitespace-pre-wrap font-sans">
              {memory.content}
            </pre>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl bg-secondary/30 p-3 text-center">
              <div className="text-sm font-bold text-foreground">{(memory.confidence_score * 100).toFixed(0)}%</div>
              <div className="text-[10px] text-muted-foreground">Confidence</div>
            </div>
            <div className="rounded-xl bg-secondary/30 p-3 text-center">
              <div className="text-sm font-bold text-foreground capitalize">{memory.memory_type.replace("_", " ")}</div>
              <div className="text-[10px] text-muted-foreground">Type</div>
            </div>
            <div className="rounded-xl bg-secondary/30 p-3 text-center">
              <div className="text-sm font-bold text-foreground">{(memory.priority || 0) > 0 ? memory.priority : "—"}</div>
              <div className="text-[10px] text-muted-foreground">Priority</div>
            </div>
          </div>

          <div className="rounded-xl border border-border p-3">
            <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-2">Metadata</div>
            <div className="space-y-1.5 text-[11px] text-muted-foreground">
              <div className="flex justify-between">
                <span>ID</span>
                <span className="font-mono text-[10px] truncate max-w-[200px]">{memory.id}</span>
              </div>
              <div className="flex justify-between">
                <span>Project</span>
                <span className="font-mono">{memory.project_id}</span>
              </div>
              <div className="flex justify-between">
                <span>Created</span>
                <span>{new Date(memory.created_at).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Pinned</span>
                <span className={memory.pinned ? "text-yellow-400" : "text-muted-foreground"}>
                  {memory.pinned ? "Yes" : "No"}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                navigator.clipboard.writeText(memory.content);
              }}
              className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-secondary/60 border border-border px-4 py-2 text-xs font-medium text-foreground hover:bg-secondary transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Copy Content
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

export function MemoryExplorer() {
  const { currentProjectId } = useProjectStore();
  const [activeTab, setActiveTab] = useState<Tab>("prompts");
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [sortField, setSortField] = useState<SortField>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");

  const tabCounts = TAB_CONFIG.reduce((acc, tab) => {
    acc[tab.id] = tab.id === "pinned"
      ? memories.filter((m) => m.pinned).length
      : memories.filter((m) => {
          const type = tab.id === "prompts" ? "prompt"
            : tab.id === "outputs" ? "output"
            : tab.id === "research" ? "research"
            : tab.id === "facts" ? "fact"
            : tab.id === "decisions" ? "decision"
            : null;
          return type && m.memory_type === type;
        }).length;
    return acc;
  }, {} as Record<string, number>);

  const loadMemories = useCallback(async () => {
    if (!currentProjectId) return;
    setLoading(true);
    try {
      let typeFilter: string | undefined;
      if (activeTab === "pinned") {
        setLoading(false);
        return;
      }
      const typeMap: Record<string, string> = {
        prompts: "prompt", outputs: "output", research: "research",
        facts: "fact", decisions: "decision",
      };
      typeFilter = typeMap[activeTab];
      const data = await projectApi.getMemories(currentProjectId, typeFilter);
      setMemories(data);
    } catch (err) {
      console.error("Failed to load memories:", err);
    } finally {
      setLoading(false);
    }
  }, [currentProjectId, activeTab]);

  const loadPinnedMemories = useCallback(async () => {
    if (!currentProjectId) return;
    try {
      const result = await projectApi.searchMemories(currentProjectId, "", 100, 0);
      setMemories(result.results.filter((m: Memory) => m.pinned));
    } catch {}
  }, [currentProjectId]);

  useEffect(() => {
    if (activeTab === "pinned") {
      loadPinnedMemories();
    } else {
      loadMemories();
    }
  }, [loadMemories, loadPinnedMemories]);

  const handleSearch = async () => {
    if (!searchQuery.trim() || !currentProjectId) return;
    setSearching(true);
    try {
      const result = await projectApi.searchMemories(currentProjectId, searchQuery);
      setMemories(result.results);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setSearching(false);
    }
  };

  const handlePin = async (memoryId: string) => {
    if (!currentProjectId) return;
    const memory = memories.find((m) => m.id === memoryId);
    if (!memory) return;
    try {
      await projectApi.pinMemory(currentProjectId, memoryId, memory.pinned ? 0 : 1);
      if (activeTab === "pinned") {
        loadPinnedMemories();
      } else {
        loadMemories();
      }
    } catch (err) {
      console.error("Failed to pin memory:", err);
    }
  };

  const handleDelete = async (memoryId: string) => {
    if (!currentProjectId || !confirm("Delete this memory?")) return;
    try {
      await projectApi.deleteMemory(currentProjectId, memoryId);
      if (activeTab === "pinned") {
        loadPinnedMemories();
      } else {
        loadMemories();
      }
    } catch (err) {
      console.error("Failed to delete memory:", err);
    }
  };

  const filteredMemories = [...memories].sort((a, b) => {
    let cmp = 0;
    switch (sortField) {
      case "date": cmp = new Date(a.created_at).getTime() - new Date(b.created_at).getTime(); break;
      case "confidence": cmp = a.confidence_score - b.confidence_score; break;
      case "type": cmp = a.memory_type.localeCompare(b.memory_type); break;
    }
    return sortDir === "asc" ? cmp : -cmp;
  });

  if (!currentProjectId) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Brain className="h-12 w-12 text-muted-foreground/20 mx-auto mb-4" />
          <h3 className="text-sm font-semibold text-foreground mb-1">No project selected</h3>
          <p className="text-xs text-muted-foreground">Select a project to explore its memory</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex-shrink-0 border-b border-border">
        <div className="flex items-center gap-3 px-4 pt-4">
          <div className="flex-1">
            <h2 className="text-base font-bold text-foreground flex items-center gap-2">
              <Brain className="h-4 w-4 text-violet-400" />
              Memory Explorer
            </h2>
            <p className="text-[10px] text-muted-foreground mt-0.5">
              {memories.length} memories in this project
            </p>
          </div>
          <button
            onClick={() => activeTab === "pinned" ? loadPinnedMemories() : loadMemories()}
            className="flex h-8 w-8 items-center justify-center rounded-xl bg-secondary/60 hover:bg-secondary transition-colors"
            title="Refresh"
          >
            <RefreshCw className={cn("h-3.5 w-3.5 text-muted-foreground", loading && "animate-spin")} />
          </button>
        </div>

        <div className="flex items-center gap-1 px-4 py-2 overflow-x-auto scrollbar-thin">
          {TAB_CONFIG.map((tab) => {
            const Icon = tab.icon;
            const count = tabCounts[tab.id] ?? 0;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[11px] font-medium whitespace-nowrap transition-all btn-press border",
                  activeTab === tab.id
                    ? "bg-violet-500/10 text-violet-400 border-violet-500/20"
                    : "text-muted-foreground border-transparent hover:bg-secondary hover:text-foreground"
                )}
              >
                <Icon className={cn("h-3.5 w-3.5", activeTab === tab.id ? tab.color : "text-current")} />
                {tab.label}
                {count > 0 && (
                  <span className={cn(
                    "text-[9px] px-1.5 py-0.5 rounded-full",
                    activeTab === tab.id ? "bg-violet-500/20 text-violet-300" : "bg-secondary"
                  )}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-2 px-4 pb-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full pl-8 pr-3 py-2 rounded-xl bg-secondary/60 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-violet-500 input-glow"
            />
          </div>
          {searchQuery && (
            <button
              onClick={() => { setSearchQuery(""); loadMemories(); }}
              className="text-[10px] text-muted-foreground hover:text-foreground"
            >
              Clear
            </button>
          )}
          <button
            onClick={handleSearch}
            disabled={searching || !searchQuery.trim()}
            className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-violet-500 to-violet-600 px-3 py-2 text-[11px] font-semibold text-white hover:from-violet-400 hover:to-violet-500 transition-all btn-press disabled:opacity-50"
          >
            {searching ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Search className="h-3 w-3" />}
            Search
          </button>
          <div className="flex items-center gap-1 border border-border rounded-xl overflow-hidden">
            <button
              onClick={() => setSortField("date")}
              className={cn(
                "flex items-center gap-1 px-2 py-1.5 text-[10px] font-medium transition-colors",
                sortField === "date" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Clock className="h-3 w-3" />
            </button>
            <button
              onClick={() => setSortField("confidence")}
              className={cn(
                "flex items-center gap-1 px-2 py-1.5 text-[10px] font-medium transition-colors",
                sortField === "confidence" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <TrendingUp className="h-3 w-3" />
            </button>
            <button
              onClick={() => setSortField(sortField === "date" ? "date" : sortField)}
              className="flex items-center gap-1 px-2 py-1.5 text-[10px] font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowUpDown className="h-3 w-3" />
            </button>
          </div>
          <div className="flex items-center gap-1 border border-border rounded-xl overflow-hidden">
            <button
              onClick={() => setViewMode("list")}
              className={cn(
                "px-2 py-1.5 text-[10px] transition-colors",
                viewMode === "list" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              ≡
            </button>
            <button
              onClick={() => setViewMode("grid")}
              className={cn(
                "px-2 py-1.5 text-[10px] transition-colors",
                viewMode === "grid" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              ⊞
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className={cn("grid gap-3", viewMode === "grid" ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1")}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-32 skeleton rounded-2xl" />
            ))}
          </div>
        ) : filteredMemories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Brain className="h-12 w-12 text-muted-foreground/20 mb-4" />
            <h3 className="text-sm font-semibold text-foreground mb-1">No {activeTab === "pinned" ? "pinned" : activeTab} memories</h3>
            <p className="text-xs text-muted-foreground max-w-xs">
              {searchQuery ? "No results for your search. Try a different query." : `No ${activeTab === "pinned" ? "pinned" : activeTab} memories yet. Run a pipeline to start building memory.`}
            </p>
          </div>
        ) : (
          <div className={cn("grid gap-3", viewMode === "grid" ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" : "grid-cols-1")}>
            {filteredMemories.map((memory) => (
              <MemoryCard
                key={memory.id}
                memory={memory}
                onPin={handlePin}
                onDelete={handleDelete}
                onClick={setSelectedMemory}
                showPin={activeTab !== "pinned" || memory.pinned}
              />
            ))}
          </div>
        )}
      </div>

      {selectedMemory && (
        <MemoryDetailModal
          memory={selectedMemory}
          onClose={() => setSelectedMemory(null)}
          onPin={handlePin}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}