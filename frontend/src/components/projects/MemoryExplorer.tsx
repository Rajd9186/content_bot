'use client';

import { useEffect, useState } from 'react';
import { useProjectStore } from '@/store/project-store';
import { projectApi, type Memory } from '@/lib/projects-api';
import { Brain, Pin, Trash2, Search } from 'lucide-react';

const memoryTypeColors: Record<string, string> = {
  prompt: 'border-blue-500/30 bg-blue-500/5',
  output: 'border-emerald-500/30 bg-emerald-500/5',
  research: 'border-violet-500/30 bg-violet-500/5',
  fact: 'border-red-500/30 bg-red-500/5',
  user_preference: 'border-amber-500/30 bg-amber-500/5',
  decision: 'border-orange-500/30 bg-orange-500/5',
  summary: 'border-border bg-secondary/30',
};

export function MemoryExplorer() {
  const { currentProjectId } = useProjectStore();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!currentProjectId) {
      setMemories([]);
      return;
    }
    loadMemories();
  }, [currentProjectId, filterType]);

  const loadMemories = async () => {
    setLoading(true);
    try {
      const data = await projectApi.getMemories(
        currentProjectId!,
        filterType === 'all' ? undefined : filterType
      );
      setMemories(data);
    } catch (err) {
      console.error('Failed to load memories:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() || !currentProjectId) return;
    setSearching(true);
    try {
      const result = await projectApi.searchMemories(currentProjectId, searchQuery);
      setMemories(result.results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const handlePin = async (memoryId: string) => {
    if (!currentProjectId) return;
    try {
      await projectApi.pinMemory(currentProjectId, memoryId, 1);
      loadMemories();
    } catch (err) {
      console.error('Failed to pin memory:', err);
    }
  };

  const handleDelete = async (memoryId: string) => {
    if (!currentProjectId || !confirm('Delete this memory?')) return;
    try {
      await projectApi.deleteMemory(currentProjectId, memoryId);
      loadMemories();
    } catch (err) {
      console.error('Failed to delete memory:', err);
    }
  };

  if (!currentProjectId) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Select a project to explore memories</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4 h-full overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Memory Explorer</h2>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:border-emerald-500"
        >
          <option value="all">All Types</option>
          <option value="prompt">Prompts</option>
          <option value="output">Outputs</option>
          <option value="research">Research</option>
          <option value="fact">Facts</option>
          <option value="user_preference">Preferences</option>
          <option value="decision">Decisions</option>
          <option value="summary">Summaries</option>
        </select>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search memories..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:border-emerald-500"
        />
        <button
          onClick={handleSearch}
          disabled={searching}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 rounded text-sm text-white transition-colors flex items-center gap-2"
        >
          <Search className="w-4 h-4" />
          {searching ? 'Searching...' : 'Search'}
        </button>
      </div>

      <div className="space-y-3">
        {memories.map((memory) => {
          const colorClass = memoryTypeColors[memory.memory_type] || memoryTypeColors.summary;

          return (
            <div
              key={memory.id}
              className={`p-3 rounded-lg border ${colorClass} group`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Brain className="w-3 h-3 text-gray-400" />
                    <span className="text-xs font-medium text-gray-400 uppercase">
                      {memory.memory_type.replace('_', ' ')}
                    </span>
                    {memory.pinned && (
                      <Pin className="w-3 h-3 text-yellow-400" />
                    )}
                  </div>
                  <p className="text-sm text-gray-200 line-clamp-3">{memory.content}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    <span>Confidence: {(memory.confidence_score * 100).toFixed(0)}%</span>
                    <span>{new Date(memory.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {!memory.pinned && (
                    <button
                      onClick={() => handlePin(memory.id)}
                      className="p-1 hover:bg-yellow-900/30 rounded"
                      title="Pin memory"
                    >
                      <Pin className="w-3 h-3 text-yellow-400" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(memory.id)}
                    className="p-1 hover:bg-red-900/30 rounded"
                    title="Delete memory"
                  >
                    <Trash2 className="w-3 h-3 text-red-400" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {memories.length === 0 && !loading && (
          <p className="text-center text-gray-500 py-8">No memories found</p>
        )}
      </div>
    </div>
  );
}