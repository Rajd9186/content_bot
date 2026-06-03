'use client';

import { useEffect, useState } from 'react';
import { useProjectStore } from '@/store/project-store';
import { projectApi, type ProjectDashboard } from '@/lib/projects-api';
import { FileText, Brain, Database, Clock, DollarSign, Hash } from 'lucide-react';

export function ProjectDashboard() {
  const { currentProjectId } = useProjectStore();
  const [dashboard, setDashboard] = useState<ProjectDashboard | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!currentProjectId) {
      setDashboard(null);
      return;
    }
    setLoading(true);
    projectApi.getDashboard(currentProjectId).then(setDashboard).finally(() => setLoading(false));
  }, [currentProjectId]);

  if (!currentProjectId) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Select a project to view its dashboard</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="p-8 text-center text-red-500">
        <p>Failed to load dashboard</p>
      </div>
    );
  }

  const stats = [
    {
      label: 'Total Outputs',
      value: dashboard.total_outputs,
      icon: FileText,
      color: 'text-emerald-400',
    },
    {
      label: 'Total Memories',
      value: dashboard.total_memories,
      icon: Brain,
      color: 'text-blue-400',
    },
    {
      label: 'Total Sources',
      value: dashboard.total_sources,
      icon: Database,
      color: 'text-purple-400',
    },
    {
      label: 'Tokens Used',
      value: dashboard.total_tokens_used.toLocaleString(),
      icon: Hash,
      color: 'text-orange-400',
    },
    {
      label: 'Estimated Cost',
      value: `$${dashboard.total_cost.toFixed(2)}`,
      icon: DollarSign,
      color: 'text-green-400',
    },
    {
      label: 'Last Activity',
      value: dashboard.last_activity
        ? new Date(dashboard.last_activity).toLocaleDateString()
        : 'N/A',
      icon: Clock,
      color: 'text-gray-400',
    },
    {
      label: 'Instructions',
      value: dashboard.instructions_count,
      icon: FileText,
      color: 'text-indigo-400',
    },
    {
      label: 'Project Skills',
      value: dashboard.skills_count,
      icon: Brain,
      color: 'text-pink-400',
    },
    {
      label: 'Allowed Sources',
      value: dashboard.allowed_sources_count,
      icon: Database,
      color: 'text-cyan-400',
    },
    {
      label: 'Blocked Sources',
      value: dashboard.blocked_sources_count,
      icon: Database,
      color: 'text-red-400',
    },
    {
      label: 'Chat Sessions',
      value: dashboard.chat_sessions_count,
      icon: Hash,
      color: 'text-yellow-400',
    },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">{dashboard.project.name}</h1>
        {dashboard.project.description && (
          <p className="text-gray-400 mt-1">{dashboard.project.description}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-gray-800 rounded-lg p-4 border border-gray-700"
          >
            <div className="flex items-center gap-3">
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
              <div>
                <p className="text-sm text-gray-400">{stat.label}</p>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {dashboard.recent_workflows && dashboard.recent_workflows.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Workflows</h2>
          <div className="space-y-2">
            {dashboard.recent_workflows.slice(0, 5).map((workflow: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-gray-900 rounded">
                <span className="text-sm text-gray-300">{workflow.topic || 'Untitled'}</span>
                <span className="text-xs text-gray-500">
                  {new Date(workflow.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}