"use client";

import { cn } from "@/lib/utils";
import { PROVIDER_LABELS } from "@/lib/constants";

interface ProviderWarningProps {
  provider: string;
  inUse: boolean;
  className?: string;
}

const WARNINGS: Record<string, string> = {
  openai: "OpenAI API key not configured — queries routed to Groq",
  groq: "Groq token limit approached — consider reducing batch size",
  nvidia: "NVIDIA API key not configured — falling back to Ollama",
  ollama: "Ollama endpoint unreachable — using fallback provider",
};

export function ProviderWarning({ provider, inUse, className }: ProviderWarningProps) {
  const label = PROVIDER_LABELS[provider] ?? provider;
  const msg = WARNINGS[provider];
  if (!msg) return null;
  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2",
        className,
      )}
    >
      <svg className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
      <div className="min-w-0">
        <p className="text-[11px] font-medium text-amber-300">{label}</p>
        <p className="text-[10px] text-muted-foreground">{msg}</p>
      </div>
    </div>
  );
}
