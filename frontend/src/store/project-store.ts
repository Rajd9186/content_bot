import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { projectApi, type Project, type ProjectSummary, type Memory, type TimelineEntry } from '@/lib/projects-api';

interface ProjectState {
  projects: ProjectSummary[];
  currentProject: Project | null;
  currentProjectId: string | null;
  loading: boolean;
  error: string | null;

  // Actions
  loadProjects: () => Promise<void>;
  selectProject: (projectId: string | null) => Promise<void>;
  createProject: (name: string, description?: string) => Promise<Project>;
  updateProject: (projectId: string, data: { name?: string; description?: string; archived?: boolean }) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;
  clearError: () => void;
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      projects: [],
      currentProject: null,
      currentProjectId: null,
      loading: false,
      error: null,

      loadProjects: async () => {
        set({ loading: true, error: null });
        try {
          const projects = await projectApi.list();
          set({ projects, loading: false });
        } catch {
          set({ loading: false });
        }
      },

      selectProject: async (projectId: string | null) => {
        if (!projectId) {
          set({ currentProject: null, currentProjectId: null });
          return;
        }
        set({ loading: true, error: null, currentProjectId: projectId });
        try {
          const project = await projectApi.get(projectId);
          set({ currentProject: project, loading: false });
        } catch (err) {
          set({ error: 'Failed to load project', loading: false });
        }
      },

      createProject: async (name: string, description?: string) => {
        set({ loading: true, error: null });
        try {
          const project = await projectApi.create(name, description);
          set({ currentProject: project, currentProjectId: project.id, loading: false });
          try {
            const projects = await projectApi.list();
            set({ projects });
          } catch {
            const summary: ProjectSummary = {
              id: project.id, name: project.name, description: project.description,
              archived: project.archived, total_outputs: 0, total_memories: 0, last_activity: null,
            };
            set((state) => ({
              projects: [summary, ...state.projects.filter((p) => p.id !== project.id)],
            }));
          }
          return project;
        } catch (err) {
          set({ error: 'Failed to create project', loading: false });
          throw err;
        }
      },

      updateProject: async (projectId: string, data) => {
        set({ loading: true, error: null });
        try {
          await projectApi.update(projectId, data);
          try {
            const projects = await projectApi.list();
            set({ projects, loading: false });
          } catch {
            set({ loading: false });
          }
          if (get().currentProjectId === projectId) {
            const project = await projectApi.get(projectId);
            set({ currentProject: project });
          }
        } catch (err) {
          set({ error: 'Failed to update project', loading: false });
          throw err;
        }
      },

      deleteProject: async (projectId: string) => {
        set({ loading: true, error: null });
        try {
          await projectApi.delete(projectId);
          set({ projects: get().projects.filter((p) => p.id !== projectId), loading: false });
          if (get().currentProjectId === projectId) {
            set({ currentProject: null, currentProjectId: null });
          }
          try {
            const projects = await projectApi.list();
            set({ projects });
          } catch {
            // list refresh not critical
          }
        } catch (err) {
          set({ error: 'Failed to delete project', loading: false });
          throw err;
        }
      },

      setCurrentProject: (project) => set({ currentProject: project }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'acip-projects',
      partialize: (state) => ({ currentProjectId: state.currentProjectId }),
    }
  )
);