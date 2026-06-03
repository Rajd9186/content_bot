'use client';
import { useState } from 'react';
import { SkillsStudio } from '@/components/skills/SkillsStudio';
import { SkillAssignment } from '@/components/skills/SkillAssignment';
import { ComplianceDashboard } from '@/components/skills/ComplianceDashboard';
import { BookOpen, Link, BarChart3 } from 'lucide-react';

type Tab = 'studio' | 'assignment' | 'compliance';

export function SkillsEngineSection() {
  const [activeTab, setActiveTab] = useState<Tab>('studio');

  const tabs = [
    { id: 'studio' as Tab, label: 'Skills', icon: BookOpen },
    { id: 'assignment' as Tab, label: 'Assignment', icon: Link },
    { id: 'compliance' as Tab, label: 'Compliance', icon: BarChart3 },
  ];

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-4 md:px-6 py-3">
        <div className="flex items-center gap-2 mb-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500/20 to-violet-600/10 border border-violet-500/20">
            <BookOpen className="w-4 h-4 text-violet-400" />
          </div>
          <h1 className="text-base font-bold text-foreground md:text-lg">Skills Studio</h1>
        </div>
        <div className="flex gap-1.5 overflow-x-auto no-scrollbar">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all btn-press ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-violet-500/10 to-violet-600/5 text-violet-400 border border-violet-500/20 shadow-sm'
                    : 'text-muted-foreground hover:bg-secondary hover:text-foreground border border-transparent'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
      <div className="flex-1 min-h-0 overflow-hidden">
        {activeTab === 'studio' && <SkillsStudio />}
        {activeTab === 'assignment' && <SkillAssignment />}
        {activeTab === 'compliance' && <ComplianceDashboard />}
      </div>
    </div>
  );
}