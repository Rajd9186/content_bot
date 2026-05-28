export default function HomePage() {
  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="mx-auto max-w-3xl px-4 py-32 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          AI Content Intelligence
        </h1>
        <p className="mt-6 text-lg leading-8 text-muted-foreground">
          Multi-agent content analysis and intelligence platform.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <a
            href="/login"
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground ring-offset-background transition-colors hover:bg-primary/90"
          >
            Get started
          </a>
          <a
            href="/api/v1/docs"
            className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-8 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
          >
            API docs
          </a>
        </div>
      </div>
    </div>
  );
}
