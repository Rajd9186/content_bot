'use client';

import { useState } from 'react';
import { useProjectStore } from '@/store/project-store';
import { projectApi, type ContextAssembly } from '@/lib/projects-api';
import { Search, Brain, FileText, MessageSquare, Pin, ChevronDown, ChevronRight } from 'lucide-react';

export function ContextPreview() {
  const { currentProjectId } = useProjectStore();
  const [prompt, setPrompt] = useState('');
  const [context, setContext] = useState<ContextAssembly | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    memories: true,
    outputs: true,
    prompts: true,
  });

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handlePreview = async () => {
    if (!prompt.trim() || !currentProjectId) return;
    setLoading(true);
    try {
      const result = await projectApi.assembleContext(currentProjectId, prompt);
      setContext(result);
    } catch (err) {
      console.error('Failed to assemble context:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!currentProjectId) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Select a project to preview context</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4 h-full overflow-y-auto">
      <h2 className="text-xl font-bold text-white">Context Preview</h2>
      <p className="text-sm text-gray-400">
        See what project context would be injected into the research agent for a given prompt.
      </p>

      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Enter a prompt to preview context..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handlePreview()}
          className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 focus:outline-none focus:border-emerald-500"
        />
        <button
          onClick={handlePreview}
          disabled={loading || !prompt.trim()}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 rounded text-sm text-white transition-colors flex items-center gap-2"
        >
          <Search className="w-4 h-4" />
          {loading ? 'Assembling...' : 'Preview'}
        </button>
      </div>

      {context && (
        <div className="space-y-4">
          <div className="p-3 rounded-lg border border-emerald-700 bg-emerald-900/10">
            <div className="flex items-center gap-2 mb-1">
              <MessageSquare className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-medium text-emerald-400 uppercase">Prompt</span>
            </div>
            <p className="text-sm text-gray-200">{context.prompt}</p>
          </div>

          <div className="border border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => toggleSection('memories')}
              className="w-full flex items-center justify-between p-3 bg-gray-800 hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-medium text-gray-200">
                  Relevant Memories ({context.relevant_memories.length})
                </span>
              </div>
              {expandedSections.memories ? (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              )}
            </button>
            {expandedSections.memories && (
              <div className="divide-y divide-gray-700">
                {context.project_context?.relevant_memories.map((mem, i) => (
                  <div key={i} className="p-3 hover:bg-gray-800/50">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-gray-400 uppercase">{mem.type}</span>
                      {mem.pinned && <Pin className="w-3 h-3 text-yellow-400" />}
                      <span className="text-xs text-gray-500 ml-auto">
                        Similarity: {(mem.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-300 line-clamp-2">{mem.content}</p>
                  </div>
                ))}
                {(!context.project_context?.relevant_memories || context.project_context.relevant_memories.length === 0) && (
                  <p className="p-3 text-sm text-gray-500">No relevant memories found</p>
                )}
              </div>
            )}
          </div>

          {context.project_context?.pinned_knowledge && context.project_context.pinned_knowledge.length > 0 && (
            <div className="border border-gray-700 rounded-lg overflow-hidden">
              <div className="flex items-center gap-2 p-3 bg-gray-800">
                <Pin className="w-4 h-4 text-yellow-400" />
                <span className="text-sm font-medium text-gray-200">
                  Pinned Knowledge ({context.project_context.pinned_knowledge.length})
                </span>
              </div>
              <div className="divide-y divide-gray-700">
                {context.project_context.pinned_knowledge.map((item, i) => (
                  <div key={i} className="p-3 hover:bg-gray-800/50">
                    <p className="text-xs text-gray-500 mb-1">{item.type}</p>
                    <p className="text-sm text-gray-300 line-clamp-2">{item.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="border border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => toggleSection('outputs')}
              className="w-full flex items-center justify-between p-3 bg-gray-800 hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-medium text-gray-200">
                  Related Outputs ({context.related_outputs.length})
                </span>
              </div>
              {expandedSections.outputs ? (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              )}
            </button>
            {expandedSections.outputs && (
              <div className="divide-y divide-gray-700">
                {context.related_outputs.map((output, i) => (
                  <div key={i} className="p-3 hover:bg-gray-800/50">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-blue-400">{output.content_type}</span>
                    </div>
                    {output.title && <p className="text-xs text-gray-400 mb-1">{output.title}</p>}
                    <p className="text-sm text-gray-300 line-clamp-2">{output.content}</p>
                  </div>
                ))}
                {context.related_outputs.length === 0 && (
                  <p className="p-3 text-sm text-gray-500">No related outputs found</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
