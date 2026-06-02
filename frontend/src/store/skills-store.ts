import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { skillsApi, type Skill, type SkillCategory } from '@/lib/skills-api';
import type { ProjectSkill } from '@/types/skills';

interface SkillsState {
  skills: Skill[];
  projectSkills: ProjectSkill[];
  selectedSkillId: string | null;
  filterCategory: SkillCategory | 'all';
  loading: boolean;

  loadSkills: (category?: string) => Promise<void>;
  loadProjectSkills: (projectId: string) => Promise<void>;
  setSelectedSkill: (id: string | null) => void;
  setFilterCategory: (cat: SkillCategory | 'all') => void;
  deleteSkill: (id: string) => Promise<void>;
}

export const useSkillsStore = create<SkillsState>()(
  persist(
    (set, get) => ({
      skills: [],
      projectSkills: [],
      selectedSkillId: null,
      filterCategory: 'all' as const,
      loading: false,

      loadSkills: async (category?: string) => {
        set({ loading: true });
        try {
          const activeOnly = category === undefined;
          const skills = await skillsApi.list(
            category === 'all' ? undefined : category,
            activeOnly
          );
          set({ skills, loading: false });
        } catch {
          set({ loading: false });
        }
      },

      loadProjectSkills: async (projectId: string) => {
        set({ loading: true });
        try {
          const projectSkills = await skillsApi.getProjectSkills(projectId);
          set({ projectSkills, loading: false });
        } catch {
          set({ loading: false });
        }
      },

      setSelectedSkill: (id) => set({ selectedSkillId: id }),

      setFilterCategory: (cat) => set({ filterCategory: cat }),

      deleteSkill: async (id: string) => {
        set({ loading: true });
        try {
          await skillsApi.delete(id);
          set({
            skills: get().skills.filter((s) => s.id !== id),
            selectedSkillId: get().selectedSkillId === id ? null : get().selectedSkillId,
            loading: false,
          });
        } catch {
          set({ loading: false });
          throw new Error('Failed to delete skill');
        }
      },
    }),
    {
      name: 'acip-skills',
      partialize: (state) => ({
        selectedSkillId: state.selectedSkillId,
        filterCategory: state.filterCategory,
      }),
    }
  )
);
