'use client';
import { useState } from 'react';
import { SkillsDashboard } from '@/components/skills/SkillsDashboard';
import { SkillAssignment } from '@/components/skills/SkillAssignment';
import { ComplianceDashboard } from '@/components/skills/ComplianceDashboard';
import { BookOpen, Link, BarChart3 } from 'lucide-react';

type Tab = 'dashboard' | 'assignment' | 'compliance';

export function SkillsEngineSection() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  
  const tabs = [
    { id: 'dashboard' as Tab, label: 'Skills', icon: BookOpen },
    { id: 'assignment' as Tab, label: 'Assignment', icon: Link },
    { id: 'compliance' as Tab, label: 'Compliance', icon: BarChart3 },
  ];
  
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-gray-800 px-6 py-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-emerald-400" />
          <h1 className="text-lg font-semibold text-white">Skills Engine</h1>
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
        {activeTab === 'dashboard' && <SkillsDashboard />}
        {activeTab === 'assignment' && <SkillAssignment />}
        {activeTab === 'compliance' && <ComplianceDashboard />}
      </div>
    </div>
  );
}
