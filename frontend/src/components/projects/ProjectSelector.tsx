'use client';

import { useEffect, useState } from 'react';
import { useProjectStore } from '@/store/project-store';
import { Folder, Plus, Archive, Trash2 } from 'lucide-react';

interface ProjectSelectorProps {
  onSelect?: (projectId: string | null) => void;
}

export function ProjectSelector({ onSelect }: ProjectSelectorProps) {
  const { projects, currentProjectId, loadProjects, selectProject, createProject, deleteProject } = useProjectStore();
  const [showCreate, setShowCreate] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      const project = await createProject(newProjectName.trim(), newProjectDesc.trim() || undefined);
      onSelect?.(project.id);
      setShowCreate(false);
      setNewProjectName('');
      setNewProjectDesc('');
    } catch (err) {
      console.error('Failed to create project:', err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this project?')) return;
    try {
      await deleteProject(projectId);
      onSelect?.(null);
    } catch (err) {
      console.error('Failed to delete project:', err);
    }
  };

  return (
    <div className="w-64 bg-gray-900 border-r border-gray-800 h-full overflow-y-auto">
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-gray-300">Projects</h2>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="p-1 hover:bg-gray-800 rounded transition-colors"
          >
            <Plus className="w-4 h-4 text-emerald-400" />
          </button>
        </div>

        {showCreate && (
          <form onSubmit={handleCreate} className="mt-2 space-y-2">
            <input
              type="text"
              placeholder="Project name"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              className="w-full px-2 py-1 text-sm bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-emerald-500"
              autoFocus
            />
            <input
              type="text"
              placeholder="Description (optional)"
              value={newProjectDesc}
              onChange={(e) => setNewProjectDesc(e.target.value)}
              className="w-full px-2 py-1 text-sm bg-gray-800 border border-gray-700 rounded focus:outline-none focus:border-emerald-500"
            />
            <div className="flex gap-2">
              <button
                type="submit"
                className="flex-1 px-2 py-1 text-xs bg-emerald-600 hover:bg-emerald-700 rounded transition-colors"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="flex-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      <div className="p-2 space-y-1">
        {projects.map((project) => (
          <div
            key={project.id}
            onClick={() => {
              selectProject(project.id);
              onSelect?.(project.id);
            }}
            className={`group flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
              currentProjectId === project.id
                ? 'bg-emerald-900/30 border border-emerald-700'
                : 'hover:bg-gray-800 border border-transparent'
            }`}
          >
            <Folder className={`w-4 h-4 ${project.archived ? 'text-gray-500' : 'text-emerald-400'}`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate">{project.name}</p>
              {project.description && (
                <p className="text-xs text-gray-500 truncate">{project.description}</p>
              )}
            </div>
            <button
              onClick={(e) => handleDelete(e, project.id)}
              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-900/30 rounded transition-all"
            >
              <Trash2 className="w-3 h-3 text-red-400" />
            </button>
          </div>
        ))}

        {projects.length === 0 && (
          <p className="text-xs text-gray-500 text-center py-4">No projects yet</p>
        )}
      </div>
    </div>
  );
}