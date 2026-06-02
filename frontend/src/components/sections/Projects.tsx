'use client';

import { useState } from 'react';
import { ProjectSelector } from '@/components/projects/ProjectSelector';
import { ProjectDashboard } from '@/components/projects/ProjectDashboard';
import { ProjectTimeline } from '@/components/projects/ProjectTimeline';
import { MemoryExplorer } from '@/components/projects/MemoryExplorer';
import { ContextPreview } from '@/components/projects/ContextPreview';
import { Folder, LayoutDashboard, Clock, Brain, Eye } from 'lucide-react';

type Tab = 'dashboard' | 'timeline' | 'memories' | 'context';

export function ProjectsSection() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  const tabs = [
    { id: 'dashboard' as Tab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'timeline' as Tab, label: 'Timeline', icon: Clock },
    { id: 'memories' as Tab, label: 'Memories', icon: Brain },
    { id: 'context' as Tab, label: 'Context', icon: Eye },
  ];

  return (
    <div className="flex h-full">
      <ProjectSelector onSelect={setSelectedProjectId} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="border-b border-gray-800 px-6 py-3">
          <div className="flex items-center gap-2">
            <Folder className="w-5 h-5 text-emerald-400" />
            <h1 className="text-lg font-semibold text-white">Projects</h1>
          </div>

          <div className="flex gap-2 mt-3">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-700'
                    : 'text-gray-400 hover:bg-gray-800'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {activeTab === 'dashboard' && <ProjectDashboard />}
          {activeTab === 'timeline' && <ProjectTimeline />}
          {activeTab === 'memories' && <MemoryExplorer />}
          {activeTab === 'context' && <ContextPreview />}
        </div>
      </div>
    </div>
  );
}