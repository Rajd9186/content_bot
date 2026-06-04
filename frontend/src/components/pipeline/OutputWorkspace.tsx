"use client";

import { useState, useMemo } from "react";
import {
  BookOpen, Brain, CheckCircle2, ChevronDown, ChevronRight, Cpu,
  FileOutput, List, Shield, Sparkles, X
} from "lucide-react";
import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";
import { useAgentNodes } from "@/hooks/use-agent-nodes";

const NODE_LABELS: Record<string, string> = {
  skill_retrieval: "Skill Retrieval",
  memory_retrieval: "Memory Retrieval",
  research: "Research",
  planner: "Planner",
  writer: "Writer",
  seo: "SEO",
  fact_checker: "Fact Check",
  compliance: "Compliance",
  review: "Review",
  finalizer: "Final Output",
};

function OutlineItem({ text }: { text: string }) {
  const isHeading = text.startsWith("# ");
  const isSubheading = text.startsWith("## ") || text.startsWith("### ");

  if (isHeading) {
    return (
      <div className="text-sm font-bold text-foreground py-1 px-2 rounded hover:bg-secondary/30 transition-colors">
        {text.replace(/^#+\s*/, "")}
      </div>
    );
  }
  if (isSubheading) {
    return (
      <div className="text-[11px] font-semibold text-foreground/75 py-0.5 px-2">
        {text.replace(/^#+\s*/, "")}
      </div>
    );
  }
  return (
    <div className="text-[11px] text-muted-foreground py-0.5 px-2 pl-6">
      {text}
    </div>
  );
}

function generateOutline(content: string): string[] {
  if (!content) return [];
  return content.split("\n")
    .filter((l) => l.trim())
    .filter((l) => l.startsWith("#") || l.trim().length > 10)
    .slice(0, 25);
}

interface CollapsibleSectionProps {
  id: string;
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function CollapsibleSection({ id, icon, label, children, defaultOpen = true }: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-border/40 last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full px-3 py-2 hover:bg-secondary/30 transition-colors"
      >
        {open ? <ChevronDown className="h-3 w-3 text-muted-foreground" /> : <ChevronRight className="h-3 w-3 text-muted-foreground" />}
        <span className="text-[11px] font-semibold text-foreground">{label}</span>
      </button>
      {open && <div className="px-3 pb-3">{children}</div>}
    </div>
  );
}

function MetadataPanel({ agentNodes }: { agentNodes: ReturnType<typeof useAgentNodes> }) {
  const nodesWithData = agentNodes.filter((n) => n.tokens_used > 0 || n.latency_ms > 0);
  const totalTokens = agentNodes.reduce((sum, n) => sum + (n.tokens_used || 0), 0);
  const totalLatency = agentNodes.reduce((sum, n) => sum + (n.latency_ms || 0), 0);
  const avgSuccess = nodesWithData.length > 0
    ? (nodesWithData.filter((n) => n.status !== "failed").length / nodesWithData.length * 100).toFixed(0)
    : null;

  const getAgentIcon = (nodeName: string) => {
    switch (nodeName) {
      case "research": return <Search className="h-3 w-3 text-blue-400" />;
      case "writer": return <FileOutput className="h-3 w-3 text-emerald-400" />;
      case "seo": return <Sparkles className="h-3 w-3 text-amber-400" />;
      case "fact_checker": return <CheckCircle2 className="h-3 w-3 text-red-400" />;
      case "compliance": return <Shield className="h-3 w-3 text-violet-400" />;
      default: return <Cpu className="h-3 w-3 text-muted-foreground" />;
    }
  };

  const Search = (props: any) => <div {...props} />;
  void Search;

  return (
    <div className="rounded-2xl border border-border bg-card/40 h-full overflow-y-auto">
      <div className="p-3 border-b border-border">
        <h3 className="text-xs font-semibold text-foreground">Content Intelligence</h3>
      </div>

      <div className="p-3 border-b border-border/40 space-y-3">
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center rounded-xl bg-secondary/40 p-2">
            <div className="text-sm font-bold text-foreground">{totalTokens > 0 ? totalTokens.toLocaleString() : "—"}</div>
            <div className="text-[9px] text-muted-foreground">Tokens</div>
          </div>
          <div className="text-center rounded-xl bg-secondary/40 p-2">
            <div className="text-sm font-bold text-foreground">
              {totalLatency > 0 ? `${(totalLatency / 1000).toFixed(1)}s` : "—"}
            </div>
            <div className="text-[9px] text-muted-foreground">Latency</div>
          </div>
          <div className="text-center rounded-xl bg-secondary/40 p-2">
            <div className="text-sm font-bold text-foreground">{avgSuccess ?? "—"}%</div>
            <div className="text-[9px] text-muted-foreground">Success</div>
          </div>
        </div>
      </div>

      <div>
        <CollapsibleSection id="agents" icon={<Cpu className="h-3 w-3" />} label="Agents Used">
          <div className="space-y-1.5">
            {agentNodes.length === 0 ? (
              <p className="text-[10px] text-muted-foreground">No agent data</p>
            ) : (
              agentNodes.map((node) => (
                <div key={node.name} className="flex items-center gap-2 rounded-lg bg-secondary/30 p-2">
                  {getAgentIcon(node.name)}
                  <div className="flex-1 min-w-0">
                    <div className="text-[11px] font-medium text-foreground">
                      {NODE_LABELS[node.name] ?? node.name}
                    </div>
                    <div className="text-[9px] text-muted-foreground">
                      {node.provider && node.model ? `${node.provider}/${node.model}` : "—"}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-[10px] text-muted-foreground">
                      {node.tokens_used ? `${(node.tokens_used / 1000).toFixed(1)}K` : "—"} tok
                    </div>
                    <div className="text-[9px] text-muted-foreground">
                      {node.latency_ms ? `${(node.latency_ms / 1000).toFixed(1)}s` : "—"}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CollapsibleSection>

        <CollapsibleSection id="skills" icon={<Sparkles className="h-3 w-3" />} label="Skills Applied">
          <div className="space-y-1">
            {agentNodes.filter((n) => n.output && Object.keys(n.output).length > 0).length === 0 ? (
              <p className="text-[10px] text-muted-foreground">No skills data</p>
            ) : (
              agentNodes.filter((n) => n.output && Object.keys(n.output).length > 0).map((node) => (
                <div key={node.name} className="flex items-center gap-2 rounded-lg bg-violet-500/5 p-2">
                  <Sparkles className="h-3 w-3 text-violet-400" />
                  <span className="text-[11px] text-foreground">{NODE_LABELS[node.name] ?? node.name}</span>
                  <span className="ml-auto text-[9px] text-muted-foreground">{Object.keys(node.output).length} outputs</span>
                </div>
              ))
            )}
          </div>
        </CollapsibleSection>

        <CollapsibleSection id="memories" icon={<Brain className="h-3 w-3" />} label="Memories Retrieved">
          <p className="text-[10px] text-muted-foreground">Memory data available in project workspace</p>
        </CollapsibleSection>

        <CollapsibleSection id="facts" icon={<CheckCircle2 className="h-3 w-3" />} label="Fact Checks">
          {agentNodes.find((n) => n.name === "fact_checker") ? (
            <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 p-2">
              <div className="text-[11px] text-emerald-400 font-medium flex items-center gap-1.5">
                <CheckCircle2 className="h-3 w-3" />
                Fact check completed
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">
                {agentNodes.find((n) => n.name === "fact_checker")?.tokens_used?.toLocaleString() || 0} tokens ·{" "}
                {(() => {
                  const ms = agentNodes.find((n) => n.name === "fact_checker")?.latency_ms || 0;
                  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
                })()}
              </div>
            </div>
          ) : (
            <p className="text-[10px] text-muted-foreground">No fact check data</p>
          )}
        </CollapsibleSection>

        <CollapsibleSection id="compliance" icon={<Shield className="h-3 w-3" />} label="Compliance">
          {agentNodes.find((n) => n.name === "compliance") ? (
            <div className="rounded-lg bg-violet-500/5 border border-violet-500/20 p-2">
              <div className="text-[11px] text-violet-400 font-medium flex items-center gap-1.5">
                <Shield className="h-3 w-3" />
                Compliance verified
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">
                {agentNodes.find((n) => n.name === "compliance")?.tokens_used?.toLocaleString() || 0} tokens
              </div>
            </div>
          ) : (
            <p className="text-[10px] text-muted-foreground">No compliance data</p>
          )}
        </CollapsibleSection>

        <CollapsibleSection id="provider" icon={<Cpu className="h-3 w-3" />} label="Provider Details">
          <div className="space-y-1">
            {agentNodes.filter((n) => n.provider).map((node) => (
              <div key={node.name} className="text-[10px]">
                <span className="text-muted-foreground">{NODE_LABELS[node.name] ?? node.name}:</span>{" "}
                <span className="text-foreground capitalize">{node.provider}</span>
                {node.model && <span className="text-muted-foreground"> / {node.model}</span>}
              </div>
            ))}
            {!agentNodes.some((n) => n.provider) && (
              <p className="text-[10px] text-muted-foreground">No provider data</p>
            )}
          </div>
        </CollapsibleSection>
      </div>
    </div>
  );
}

export function OutputWorkspace() {
  const content = usePipelineStore((s) => s.content);
  const agentNodes = useAgentNodes();

  const stripFences = (s: string) => s.replace(/^```markdown\s*/gm, "").replace(/^```\s*$/gm, "").trim();
  const finalContent = content?.final_content ? stripFences(content.final_content) : null;
  const draftContent = content?.draft_content ? stripFences(content.draft_content) : null;
  const displayContent = finalContent ?? draftContent ?? "";

  const outline = useMemo(() => generateOutline(displayContent), [displayContent]);

  if (!displayContent && agentNodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <FileOutput className="h-12 w-12 text-muted-foreground/20 mx-auto mb-4" />
          <h3 className="text-sm font-semibold text-foreground mb-1">No output yet</h3>
          <p className="text-xs text-muted-foreground">Run a pipeline to see generated content</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-[180px_1fr_220px] lg:grid-cols-[220px_1fr_260px] gap-4 h-full min-h-0">
      <div className="rounded-2xl border border-border bg-card/40 h-full overflow-y-auto">
        <div className="p-3 border-b border-border sticky top-0 bg-card/80 backdrop-blur-sm z-10">
          <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
            <List className="h-3.5 w-3.5 text-violet-400" />
            Outline
          </h3>
        </div>
        <div className="p-3 space-y-0.5">
          {outline.length === 0 ? (
            <p className="text-[10px] text-muted-foreground text-center py-4">No outline available</p>
          ) : (
            outline.map((item, i) => (
              <OutlineItem key={i} text={item} />
            ))
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-border bg-card/40 h-full overflow-y-auto">
        <div className="p-3 border-b border-border sticky top-0 bg-card/80 backdrop-blur-sm z-10 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
            <BookOpen className="h-3.5 w-3.5 text-emerald-400" />
            Generated Content
          </h3>
          <div className="flex items-center gap-2">
            {content?.word_count && (
              <span className="text-[10px] text-muted-foreground">{content.word_count.toLocaleString()} words</span>
            )}
            {finalContent && (
              <span className="text-[10px] text-emerald-400 font-medium">Final</span>
            )}
          </div>
        </div>
        <div className="p-4">
          {displayContent ? (
            <pre className="whitespace-pre-wrap text-[13px] leading-relaxed text-foreground/90 font-sans">
              {displayContent}
            </pre>
          ) : (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="space-y-1.5">
                  <div className="h-4 w-3/4 skeleton rounded" />
                  <div className="h-3 w-full skeleton rounded" />
                  <div className="h-3 w-5/6 skeleton rounded" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <MetadataPanel agentNodes={agentNodes} />
    </div>
  );
}