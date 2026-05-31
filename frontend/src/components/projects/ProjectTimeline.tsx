'use client';

import { useEffect, useState } from 'react';
import { useProjectStore } from '@/store/project-store';
import { projectApi, type TimelineEntry } from '@/lib/projects-api';
import { FileText, MessageSquare, Brain, Workflow } from 'lucide-react';

const typeIcons: Record<string, any> = {
  prompt: MessageSquare,
  output: FileText,
  memory: Brain,
  workflow: Workflow,
};

const typeColors: Record<string, string> = {
  prompt: 'text-blue-400 bg-blue-900/20 border-blue-700',
  output: 'text-emerald-400 bg-emerald-900/20 border-emerald-700',
  memory: 'text-purple-400 bg-purple-900/20 border-purple-700',
  workflow: 'text-orange-400 bg-orange-900/20 border-orange-700',
};

export function ProjectTimeline() {
  const { currentProjectId } = useProjectStore();
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!currentProjectId) {
      setTimeline([]);
      return;
    }
    setLoading(true);
    projectApi.getTimeline(currentProjectId).then(setTimeline).finally(() => setLoading(false));
  }, [currentProjectId]);

  if (!currentProjectId) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Select a project to view its timeline</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Loading timeline...</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-bold text-white">Project Timeline</h2>

      <div className="space-y-3">
        {timeline.map((entry) => {
          const Icon = typeIcons[entry.type] || FileText;
          const colorClass = typeColors[entry.type] || typeColors.output;

          return (
            <div
              key={entry.id}
              className={`flex items-start gap-3 p-3 rounded-lg border ${colorClass}`}
            >
              <Icon className="w-5 h-5 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-white">{entry.title}</h3>
                  <span className="text-xs text-gray-400">
                    {new Date(entry.created_at).toLocaleString()}
                  </span>
                </div>
                {entry.description && (
                  <p className="text-sm text-gray-300 mt-1 line-clamp-2">{entry.description}</p>
                )}
                {entry.metadata && Object.keys(entry.metadata).length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Object.entries(entry.metadata).slice(0, 3).map(([key, value]) => (
                      <span key={key} className="text-xs px-2 py-0.5 bg-gray-800 rounded">
                        {key}: {String(value).slice(0, 50)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {timeline.length === 0 && (
          <p className="text-center text-gray-500 py-8">No activity yet</p>
        )}
      </div>
    </div>
  );
}