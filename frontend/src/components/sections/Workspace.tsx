export function Workspace() {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card/30 p-5">
        <h3 className="text-sm font-semibold text-foreground">Workspace</h3>
        <p className="mt-2 text-xs text-muted-foreground">
          Manage your workspace settings, team members, and API keys.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <h4 className="text-xs font-semibold text-foreground mb-3">Team Members</h4>
          <p className="text-[10px] text-muted-foreground">No team members configured yet.</p>
        </div>
        <div className="rounded-xl border border-border bg-card/30 p-4">
          <h4 className="text-xs font-semibold text-foreground mb-3">API Keys</h4>
          <p className="text-[10px] text-muted-foreground">No API keys configured yet.</p>
        </div>
      </div>
    </div>
  );
}
