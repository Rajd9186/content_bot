"use client";

import dynamic from "next/dynamic";
import { useUIStore } from "@/store/ui-store";

const SideNav = dynamic(() => import("@/components/layout/SideNav").then((m) => ({ default: m.SideNav })), { ssr: false });
const TopNav = dynamic(() => import("@/components/layout/TopNav").then((m) => ({ default: m.TopNav })), { ssr: false });
const Footer = dynamic(() => import("@/components/layout/Footer").then((m) => ({ default: m.Footer })), { ssr: false });

const SECTION_LABELS: Record<string, string> = {
  pipeline: "Content Pipeline",
  history: "Pipeline History",
  analytics: "Analytics",
  workspace: "Workspace",
  settings: "Settings",
  agents: "Agent Monitor",
  orchestration: "Orchestration",
  metrics: "System Metrics",
  skills: "Skills Engine",
  operations: "Operations",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const section = useUIStore((s) => s.section);

  return (
    <div className="flex h-screen bg-background">
      <SideNav />
      <div className="flex flex-1 flex-col min-w-0">
        <TopNav>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground/60">/</span>
            <span className="text-xs font-medium text-foreground">{SECTION_LABELS[section] ?? section}</span>
          </div>
        </TopNav>
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
        <Footer />
      </div>
    </div>
  );
}
