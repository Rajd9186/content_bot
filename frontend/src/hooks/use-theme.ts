"use client";

import { useUIStore } from "@/store/ui-store";

export function useTheme() {
  const theme = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);
  const toggleTheme = useUIStore((s) => s.toggleTheme);

  return { theme, isDark: theme === "dark", setTheme, toggleTheme };
}
