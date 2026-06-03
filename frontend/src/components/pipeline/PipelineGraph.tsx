"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";
import { ChevronRight } from "lucide-react";

const STAGE_LABELS: Record<string, string> = {
  skill_retrieval: "Skill Retrieval",
  memory_retrieval: "Memory Retrieval",
  research: "Research",
  planner: "Planner",
  source_ranking: "Source Ranking",
  fact_checker: "Fact Check",
  seo: "SEO",
  writer: "Writer",
  compliance: "Compliance",
  review: "Review",
  finalizer: "Finalizer",
};

const PIPELINE_NODES = [
  { id: "prompt", label: "Prompt", type: "input" as const },
  { id: "skill_retrieval", label: "Skill Retrieval", type: "agent" as const },
  { id: "memory_retrieval", label: "Memory Retrieval", type: "agent" as const },
  { id: "research", label: "Research", type: "agent" as const },
  { id: "planner", label: "Planner", type: "agent" as const },
  { id: "writer", label: "Writer", type: "agent" as const },
  { id: "seo", label: "SEO", type: "agent" as const },
  { id: "fact_checker", label: "Fact Check", type: "agent" as const },
  { id: "compliance", label: "Compliance", type: "agent" as const },
  { id: "review", label: "Review", type: "agent" as const },
  { id: "finalizer", label: "Final Output", type: "output" as const },
];

interface NodeData {
  id: string;
  label: string;
  type: "input" | "agent" | "output";
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  latency?: number;
  tokens?: number;
  provider?: string;
  model?: string;
}

function getNodeStatus(nodeId: string, events: { node?: string; type?: string }[], status: string | undefined): "pending" | "running" | "completed" | "failed" | "skipped" {
  if (status === "failed") return "failed";
  if (status === "completed" || status === "cancelled" || status === "success") return "skipped";

  const nodeEvent = events.find((e) => e.node === nodeId);
  if (!nodeEvent) return "pending";

  switch (nodeEvent.type) {
    case "node_completed":
    case "pipeline_completed":
      return "completed";
    case "node_started":
    case "node_running":
      return "running";
    case "node_failed":
    case "pipeline_failed":
      return "failed";
    default:
      return "pending";
  }
}

function NodeCard({ node, onClick }: { node: NodeData; onClick?: () => void }) {
  const statusStyles = {
    pending: "border-border bg-card/40",
    running: "border-blue-500/40 bg-blue-500/5",
    completed: "border-emerald-500/30 bg-emerald-500/5",
    failed: "border-red-500/40 bg-red-500/5",
    skipped: "border-amber-500/30 bg-amber-500/5",
  };

  const dotStyles = {
    pending: "bg-slate-500",
    running: "bg-blue-400 animate-pulse-soft",
    completed: "bg-emerald-400",
    failed: "bg-red-400",
    skipped: "bg-amber-400",
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        "relative flex flex-col items-center rounded-2xl border p-3 transition-all duration-300 min-w-[100px]",
        statusStyles[node.status],
        node.status !== "pending" && "hover:-translate-y-0.5 hover:shadow-lg",
        node.status === "running" && "node-pulse"
      )}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <span className={cn("status-dot", dotStyles[node.status])} />
        {node.type === "input" && (
          <span className="text-[10px] font-medium text-violet-400 uppercase tracking-wider">IN</span>
        )}
        {node.type === "output" && (
          <span className="text-[10px] font-medium text-emerald-400 uppercase tracking-wider">OUT</span>
        )}
      </div>
      <span className="text-[11px] font-semibold text-foreground text-center leading-tight">
        {node.label}
      </span>
      {node.latency != null && (
        <span className="text-[10px] text-muted-foreground mt-0.5">
          {node.latency < 1000 ? `${node.latency}ms` : `${(node.latency / 1000).toFixed(1)}s`}
        </span>
      )}
      {node.provider && (
        <span className="text-[9px] text-muted-foreground/60 mt-0.5 truncate max-w-full">{node.provider}</span>
      )}
    </button>
  );
}

interface PipelineGraphProps {
  onNodeClick?: (nodeId: string) => void;
}

export function PipelineGraph({ onNodeClick }: PipelineGraphProps) {
  const events = usePipelineStore((s) => s.events);
  const status = usePipelineStore((s) => s.status);

  const nodes: NodeData[] = useMemo(() => {
    return PIPELINE_NODES.map((n) => {
      const nodeEvents = events.filter((e) => e.node === n.id);
      const completedEvent = nodeEvents.find((e) => e.type === "node_completed");
      const runningEvent = nodeEvents.find((e) => e.type === "node_started" || e.type === "node_running");

      let nodeStatus: NodeData["status"] = "pending";
      if (status?.status === "failed" || status?.status === "cancelled") {
        nodeStatus = "skipped";
      } else if (completedEvent) {
        nodeStatus = "completed";
      } else if (runningEvent) {
        nodeStatus = "running";
      } else if (status?.nodes && n.id in status.nodes) {
        const nodeInfo = status.nodes[n.id];
        if (nodeInfo.status === "completed") nodeStatus = "completed";
        else if (nodeInfo.status === "running" || nodeInfo.status === "pending") nodeStatus = "running";
        else if (nodeInfo.status === "failed") nodeStatus = "failed";
      }

      const latency = completedEvent?.latency_ms ?? (nodeStatus === "completed" && status?.nodes?.[n.id] ? status.nodes[n.id].latency_ms : undefined);
      const tokens = completedEvent?.tokens_used ?? (nodeStatus === "completed" && status?.nodes?.[n.id] ? status.nodes[n.id].tokens_used : undefined);

      return {
        ...n,
        status: nodeStatus,
        latency,
        tokens,
      };
    });
  }, [events, status]);

  const isRunning = nodes.some((n) => n.status === "running");
  const completedCount = nodes.filter((n) => n.status === "completed").length;
  const totalCount = nodes.length;

  const EDGES = [
    ["prompt", "skill_retrieval"],
    ["prompt", "memory_retrieval"],
    ["skill_retrieval", "research"],
    ["memory_retrieval", "research"],
    ["research", "planner"],
    ["planner", "writer"],
    ["writer", "seo"],
    ["seo", "fact_checker"],
    ["fact_checker", "compliance"],
    ["compliance", "review"],
    ["review", "finalizer"],
  ];

  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));

  const getStatusColor = (fromId: string, toId: string) => {
    const from = nodeMap[fromId];
    const to = nodeMap[toId];
    if (from?.status === "completed" && to?.status === "completed") return "stroke-emerald-400";
    if (from?.status === "completed" && to?.status === "running") return "stroke-blue-400";
    if (from?.status === "completed") return "stroke-violet-400/50";
    return "stroke-border";
  };

  const nodePositions: Record<string, { col: number; row: number }> = {
    prompt: { col: 0, row: 0 },
    skill_retrieval: { col: 1, row: 0 },
    memory_retrieval: { col: 1, row: 1 },
    research: { col: 2, row: 0 },
    planner: { col: 2, row: 1 },
    writer: { col: 3, row: 0 },
    seo: { col: 3, row: 1 },
    fact_checker: { col: 4, row: 0 },
    compliance: { col: 4, row: 1 },
    review: { col: 5, row: 0 },
    finalizer: { col: 6, row: 0 },
  };

  const COL_COUNT = 7;
  const ROW_COUNT = 2;
  const CELL_W = 140;
  const CELL_H = 100;
  const PADDING_X = 40;
  const PADDING_Y = 20;

  const svgW = PADDING_X * 2 + COL_COUNT * CELL_W;
  const svgH = PADDING_Y * 2 + ROW_COUNT * CELL_H;

  const getNodeCenter = (nodeId: string, which: "top" | "bottom" | "left" | "right") => {
    const pos = nodePositions[nodeId];
    if (!pos) return { x: 0, y: 0 };
    const cx = PADDING_X + pos.col * CELL_W + CELL_W / 2;
    const cy = PADDING_Y + pos.row * CELL_H + CELL_H / 2;
    switch (which) {
      case "top": return { x: cx, y: cy - CELL_H / 2 };
      case "bottom": return { x: cx, y: cy + CELL_H / 2 };
      case "left": return { x: cx - CELL_W / 2, y: cy };
      case "right": return { x: cx + CELL_W / 2, y: cy };
    }
  };

  const getEdgePath = (fromId: string, toId: string) => {
    const fromPos = nodePositions[fromId];
    const toPos = nodePositions[toId];
    if (!fromPos || !toPos) return "";

    const fx = PADDING_X + fromPos.col * CELL_W + CELL_W / 2;
    const fy = PADDING_Y + fromPos.row * CELL_H + CELL_H;
    const tx = PADDING_X + toPos.col * CELL_W + CELL_W / 2;
    const ty = PADDING_Y + toPos.row * CELL_H;

    if (fromPos.col === toPos.col) {
      return `M ${fx} ${fy} L ${tx} ${ty}`;
    }

    const midY = (fy + ty) / 2;
    return `M ${fx} ${fy} C ${fx} ${midY} ${tx} ${midY} ${tx} ${ty}`;
  };

  return (
    <div className="w-full overflow-x-auto">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-semibold text-foreground">Pipeline Graph</h3>
          {isRunning && (
            <span className="flex items-center gap-1 text-[10px] text-blue-400">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse" />
              Running
            </span>
          )}
        </div>
        <span className="text-[10px] text-muted-foreground">
          {completedCount}/{totalCount} stages completed
        </span>
      </div>

      <div className="relative rounded-2xl border border-border bg-card/20 p-4 overflow-x-auto">
        <svg
          width={svgW}
          height={svgH}
          viewBox={`0 0 ${svgW} ${svgH}`}
          className="hidden sm:block"
          style={{ minWidth: svgW }}
        >
          <defs>
            <linearGradient id="edge-gradient-active" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="hsl(262, 83%, 58%)" />
              <stop offset="100%" stopColor="hsl(160, 84%, 39%)" />
            </linearGradient>
            <linearGradient id="edge-gradient-running" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="hsl(217, 91%, 70%)" />
              <stop offset="100%" stopColor="hsl(262, 83%, 58%)" />
            </linearGradient>
            <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="hsl(var(--border))" />
            </marker>
            <marker id="arrow-active" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="hsl(262, 83%, 58%)" />
            </marker>
            <marker id="arrow-emerald" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="hsl(160, 84%, 39%)" />
            </marker>
          </defs>

          {EDGES.map(([from, to]) => {
            const fromNode = nodeMap[from];
            const toNode = nodeMap[to];
            const isActive = fromNode?.status === "completed" && toNode?.status === "completed";
            const isRunning = fromNode?.status === "completed" && toNode?.status === "running";
            const color = getStatusColor(from, to);
            const path = getEdgePath(from, to);

            return (
              <path
                key={`${from}-${to}`}
                d={path}
                fill="none"
                className={cn(
                  "transition-all duration-500",
                  color,
                  isActive && "stroke-[2.5] opacity-80",
                  isRunning && "stroke-[2] opacity-60",
                )}
                strokeWidth={isActive || isRunning ? 2 : 1}
                strokeDasharray={!isActive && !isRunning ? "4 3" : undefined}
                markerEnd={isActive ? "url(#arrow-emerald)" : isRunning ? "url(#arrow-active)" : "url(#arrow)"}
              />
            );
          })}

          {nodes.map((node) => {
            const pos = nodePositions[node.id];
            if (!pos) return null;
            const x = PADDING_X + pos.col * CELL_W;
            const y = PADDING_Y + pos.row * CELL_H;
            const statusColors: Record<string, string> = {
              pending: "border-border bg-card/40",
              running: "border-blue-500/40 bg-blue-500/5",
              completed: "border-emerald-500/30 bg-emerald-500/5",
              failed: "border-red-500/40 bg-red-500/5",
              skipped: "border-amber-500/30 bg-amber-500/5",
            };
            const glowColors: Record<string, string> = {
              pending: "",
              running: "shadow-[0_0_12px_rgba(59,130,246,0.3)]",
              completed: "shadow-[0_0_12px_rgba(16,185,129,0.2)]",
              failed: "shadow-[0_0_12px_rgba(239,68,68,0.3)]",
              skipped: "",
            };

            return (
              <foreignObject
                key={node.id}
                x={x + 8}
                y={y + 8}
                width={CELL_W - 16}
                height={CELL_H - 16}
                className="overflow-visible"
              >
                <button
                  onClick={() => onNodeClick?.(node.id)}
                  onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onNodeClick?.(node.id)}
                  aria-label={`${node.label} - ${node.status}`}
                  aria-pressed={false}
                  role="button"
                  tabIndex={0}
                  className={cn(
                    "w-full h-full flex flex-col items-center justify-center rounded-2xl border p-2.5 transition-all duration-300",
                    statusColors[node.status],
                    glowColors[node.status],
                    node.status !== "pending" && "hover:-translate-y-0.5 hover:shadow-lg cursor-pointer",
                    node.status === "running" && "animate-pulse",
                  )}
                >
                  <div className="flex items-center gap-1 mb-0.5">
                    <span className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      node.status === "pending" && "bg-slate-500",
                      node.status === "running" && "bg-blue-400",
                      node.status === "completed" && "bg-emerald-400",
                      node.status === "failed" && "bg-red-400",
                      node.status === "skipped" && "bg-amber-400",
                    )} />
                    {node.type === "input" && (
                      <span className="text-[8px] font-bold text-violet-400">IN</span>
                    )}
                    {node.type === "output" && (
                      <span className="text-[8px] font-bold text-emerald-400">OUT</span>
                    )}
                  </div>
                  <span className="text-[10px] font-semibold text-foreground text-center leading-tight">
                    {node.label}
                  </span>
                  {node.latency != null && (
                    <span className="text-[9px] text-muted-foreground mt-0.5">
                      {node.latency < 1000 ? `${node.latency}ms` : `${(node.latency / 1000).toFixed(1)}s`}
                    </span>
                  )}
                  {node.tokens != null && node.tokens > 0 && (
                    <span className="text-[9px] text-muted-foreground/70">
                      {node.tokens.toLocaleString()} tok
                    </span>
                  )}
                </button>
              </foreignObject>
            );
          })}
        </svg>

        <div className="sm:hidden flex flex-col gap-2">
          {nodes.map((node) => (
            <div key={node.id} className="flex items-center gap-2">
              {node.id !== "prompt" && (
                <div className="flex-1 h-px bg-border" />
              )}
              <NodeCard
                node={node}
                onClick={() => onNodeClick?.(node.id)}
              />
              {node.id !== "finalizer" && (
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40" />
              )}
            </div>
          ))}
        </div>

        <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border/40">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-slate-500" />
            <span className="text-[10px] text-muted-foreground">Pending</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="text-[10px] text-muted-foreground">Running</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-[10px] text-muted-foreground">Completed</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-400" />
            <span className="text-[10px] text-muted-foreground">Failed</span>
          </div>
        </div>
      </div>
    </div>
  );
}