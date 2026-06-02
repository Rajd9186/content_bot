"use client";

import dynamic from "next/dynamic";
import { useUIStore } from "@/store/ui-store";

const ContentPipeline = dynamic(() => import("@/components/sections/ContentPipeline").then((m) => ({ default: m.ContentPipeline })), { ssr: false });
const PipelineListSection = dynamic(() => import("@/components/sections/PipelineListSection").then((m) => ({ default: m.PipelineListSection })), { ssr: false });
const Analytics = dynamic(() => import("@/components/sections/Analytics").then((m) => ({ default: m.Analytics })), { ssr: false });
const Workspace = dynamic(() => import("@/components/sections/Workspace").then((m) => ({ default: m.Workspace })), { ssr: false });
const Settings = dynamic(() => import("@/components/sections/Settings").then((m) => ({ default: m.Settings })), { ssr: false });
const AgentMonitor = dynamic(() => import("@/components/sections/AgentMonitor").then((m) => ({ default: m.AgentMonitor })), { ssr: false });
const Orchestration = dynamic(() => import("@/components/sections/Orchestration").then((m) => ({ default: m.Orchestration })), { ssr: false });
const SystemMetrics = dynamic(() => import("@/components/sections/SystemMetrics").then((m) => ({ default: m.SystemMetrics })), { ssr: false });
const ProjectsSection = dynamic(() => import("@/components/sections/Projects").then((m) => ({ default: m.ProjectsSection })), { ssr: false });
const SkillsEngineSection = dynamic(() => import("@/components/sections/SkillsEngine").then((m) => ({ default: m.SkillsEngineSection })), { ssr: false });
const OperationsSection = dynamic(() => import("@/components/sections/Operations").then((m) => ({ default: m.OperationsSection })), { ssr: false });

const SECTIONS: Record<string, React.ComponentType> = {
  pipeline: ContentPipeline,
  history: PipelineListSection,
  analytics: Analytics,
  workspace: Workspace,
  settings: Settings,
  agents: AgentMonitor,
  orchestration: Orchestration,
  metrics: SystemMetrics,
  projects: ProjectsSection,
  skills: SkillsEngineSection,
  operations: OperationsSection,
};

export default function DashboardPage() {
  const section = useUIStore((s) => s.section);
  const Component = SECTIONS[section] ?? ContentPipeline;

  return (
    <div className="h-full min-h-0">
      <Component />
    </div>
  );
}
