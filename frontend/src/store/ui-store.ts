import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { SectionName, SettingsState } from "@/types/api";

interface UIState {
  section: SectionName;
  sidebarOpen: boolean;
  theme: "dark" | "light";
  mobileMenuOpen: boolean;
  modal: string | null;
  settings: SettingsState;
  setSection: (s: SectionName) => void;
  toggleSidebar: () => void;
  setTheme: (t: "dark" | "light") => void;
  toggleTheme: () => void;
  setMobileMenuOpen: (open: boolean) => void;
  openModal: (id: string) => void;
  closeModal: () => void;
  updateSettings: (s: Partial<SettingsState>) => void;
}

const defaultSettings: SettingsState = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000",
  refreshInterval: 5,
  telemetryEnabled: true,
  defaultTone: "professional",
  defaultAudience: "general",
};

function applyTheme(theme: "dark" | "light") {
  if (typeof document !== "undefined") {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      section: "commandCenter",
      sidebarOpen: true,
      theme: "dark",
      mobileMenuOpen: false,
      modal: null,
      settings: defaultSettings,
      setSection: (section) => set({ section, mobileMenuOpen: false }),
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setTheme: (theme) => {
        applyTheme(theme);
        set({ theme });
      },
      toggleTheme: () =>
        set((s) => {
          const next = s.theme === "dark" ? "light" : "dark";
          applyTheme(next);
          return { theme: next };
        }),
      setMobileMenuOpen: (mobileMenuOpen) => set({ mobileMenuOpen }),
      openModal: (modal) => set({ modal }),
      closeModal: () => set({ modal: null }),
      updateSettings: (partial) =>
        set((s) => ({ settings: { ...s.settings, ...partial } })),
    }),
    {
      name: "acip-ui",
      onRehydrateStorage: () => (state) => {
        if (state) applyTheme(state.theme);
      },
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
        settings: state.settings,
      }),
    },
  ),
);