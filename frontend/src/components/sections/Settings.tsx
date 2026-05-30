"use client";

import { useUIStore } from "@/store/ui-store";

export function Settings() {
  const theme = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);
  const settings = useUIStore((s) => s.settings);
  const updateSettings = useUIStore((s) => s.updateSettings);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card/30 p-5">
        <h3 className="text-sm font-semibold text-foreground">Settings</h3>
      </div>

      <div className="rounded-xl border border-border bg-card/30 p-4">
        <h4 className="text-xs font-semibold text-foreground mb-4">Appearance</h4>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-foreground">Theme</p>
            <p className="text-[10px] text-muted-foreground">Dark mode is default for this platform</p>
          </div>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as "dark" | "light")}
            className="rounded-lg border border-border bg-black/20 px-3 py-1.5 text-xs text-foreground"
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card/30 p-4">
        <h4 className="text-xs font-semibold text-foreground mb-4">Notifications</h4>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-foreground">Refresh Interval</p>
            <p className="text-[10px] text-muted-foreground">How often to check for updates</p>
          </div>
          <select
            value={settings.refreshInterval}
            onChange={(e) => updateSettings({ refreshInterval: Number(e.target.value) })}
            className="rounded-lg border border-border bg-black/20 px-3 py-1.5 text-xs text-foreground"
          >
            <option value={5}>5s</option>
            <option value={10}>10s</option>
            <option value={30}>30s</option>
            <option value={60}>60s</option>
          </select>
        </div>
      </div>
    </div>
  );
}
