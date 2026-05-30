export function Footer() {
  return (
    <footer className="flex items-center justify-between border-t border-border bg-card/20 px-6 py-3 text-[10px] text-muted-foreground">
      <span>© {new Date().getFullYear()} ACIP — AI Content Intelligence Platform</span>
      <div className="flex items-center gap-4">
        <span>v1.0.0</span>
      </div>
    </footer>
  );
}
