export function Footer() {
  return (
    <footer className="flex items-center justify-between border-t border-border bg-secondary/30 px-6 py-3 text-[11px] text-muted-foreground">
      <span>© {new Date().getFullYear()} ACIP — AI Content Intelligence Platform</span>
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse-soft" />
          All systems operational
        </span>
        <span className="text-border">|</span>
        <span>v1.0.0</span>
      </div>
    </footer>
  );
}