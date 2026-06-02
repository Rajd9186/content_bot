'use client';

import { useEffect, useState } from 'react';
import { Gauge, RefreshCw, Activity, Zap, Clock, CheckCircle2, AlertCircle } from 'lucide-react';

interface ProviderStats {
  provider: string;
  rpm_used: number;
  rpm_limit: number;
  tpm_used: number;
  tpm_limit: number;
  active_requests: number;
  queue_length: number;
  capacity_remaining: number;
  circuit_state: string;
  average_latency: number;
  success_rate: number;
  total_calls: number;
}

const PROVIDER_COLORS: Record<string, { border: string; bg: string; bar: string; label: string }> = {
  groq: { border: 'border-emerald-500/20', bg: 'bg-emerald-500/5', bar: 'bg-emerald-500', label: 'Groq' },
  nvidia: { border: 'border-blue-500/20', bg: 'bg-blue-500/5', bar: 'bg-blue-500', label: 'NVIDIA' },
  openai: { border: 'border-violet-500/20', bg: 'bg-violet-500/5', bar: 'bg-violet-500', label: 'OpenAI' },
  ollama: { border: 'border-orange-500/20', bg: 'bg-orange-500/5', bar: 'bg-orange-500', label: 'Ollama' },
  anthropic: { border: 'border-yellow-500/20', bg: 'bg-yellow-500/5', bar: 'bg-yellow-500', label: 'Anthropic' },
};

function CircuitBadge({ state }: { state: string }) {
  const colors = {
    closed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    half_open: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    open: 'bg-red-500/10 text-red-400 border-red-500/20',
  };
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${colors[state as keyof typeof colors] || colors.closed}`}>
      {state.toUpperCase()}
    </span>
  );
}

function UsageBar({ used, limit, label, unit }: { used: number; limit: number; label: string; unit: string }) {
  const pct = limit > 0 ? Math.min(100, (used / limit) * 100) : 0;
  const color = pct > 80 ? 'bg-red-500' : pct > 50 ? 'bg-amber-500' : 'bg-violet-500';
  const textColor = pct > 80 ? 'text-red-400' : pct > 50 ? 'text-amber-400' : 'text-violet-400';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[11px] text-muted-foreground">
        <span>{label}: {used.toLocaleString()} / {limit.toLocaleString()} {unit}</span>
        <span className={textColor}>{pct.toFixed(0)}%</span>
      </div>
      <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all duration-500 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function ProviderDashboard() {
  const [stats, setStats] = useState<Record<string, ProviderStats>>({});
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const loadStats = async () => {
    try {
      const res = await fetch('/api/providers/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch {
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  };

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const totalCalls = Object.values(stats).reduce((s, p) => s + (p.total_calls || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/20 to-violet-600/10 border border-violet-500/20">
            <Gauge className="w-4 h-4 text-violet-400" />
          </div>
          <h2 className="text-lg font-bold text-foreground">Provider Operations</h2>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-[11px] text-muted-foreground hidden sm:block">
              Updated {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={loadStats}
            className="btn-press flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground rounded-xl border border-border transition-all"
          >
            <RefreshCw className="w-3 h-3" />
            Refresh
          </button>
        </div>
      </div>

      {loading && Object.keys(stats).length === 0 && (
        <div className="flex items-center justify-center py-16">
          <div className="text-muted-foreground text-sm">Loading provider statistics...</div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(stats).map(([key, stat]) => {
          const colors = PROVIDER_COLORS[key] || { border: 'border-border', bg: 'bg-card/60', bar: 'bg-violet-500', label: key };
          return (
            <div key={key} className={`rounded-2xl border ${colors.border} ${colors.bg} p-4 space-y-4 card-hover shadow-sm`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-foreground">{colors.label}</span>
                  <CircuitBadge state={stat.circuit_state || 'closed'} />
                </div>
                <Activity className="w-4 h-4 text-muted-foreground" />
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Zap className="w-3 h-3" />
                  <span>Active: <strong className="text-foreground">{stat.active_requests}</strong></span>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  <span>Latency: <strong className="text-foreground">{(stat.average_latency || 0).toFixed(0)}ms</strong></span>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  {stat.success_rate >= 0.95 ? (
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-3 h-3 text-amber-400" />
                  )}
                  <span>Success: <strong className="text-foreground">{(stat.success_rate * 100).toFixed(1)}%</strong></span>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Activity className="w-3 h-3" />
                  <span>Calls: <strong className="text-foreground">{(stat.total_calls || 0).toLocaleString()}</strong></span>
                </div>
              </div>

              <UsageBar used={stat.rpm_used} limit={stat.rpm_limit} label="RPM" unit="" />
              <UsageBar used={stat.tpm_used} limit={stat.tpm_limit} label="TPM" unit="" />
            </div>
          );
        })}
      </div>

      {totalCalls > 0 && (
        <div className="rounded-2xl border border-border bg-card/60 p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground mb-3">Request Distribution</h3>
          <div className="flex h-3 rounded-full overflow-hidden bg-secondary gap-0.5">
            {Object.entries(stats).map(([key, stat]) => {
              const pct = totalCalls > 0 ? ((stat.total_calls || 0) / totalCalls) * 100 : 0;
              if (pct < 1) return null;
              const barColor = PROVIDER_COLORS[key]?.bar || 'bg-violet-500';
              return <div key={key} className={`${barColor} transition-all rounded-full`} style={{ width: `${pct}%` }} />;
            })}
          </div>
          <div className="flex flex-wrap gap-4 mt-3 text-xs text-muted-foreground">
            {Object.entries(stats).map(([key, stat]) => {
              const pct = totalCalls > 0 ? ((stat.total_calls || 0) / totalCalls) * 100 : 0;
              const colors = PROVIDER_COLORS[key] || { bar: 'bg-violet-500', label: key };
              return (
                <div key={key} className="flex items-center gap-1.5">
                  <div className={`w-2 h-2 rounded-full ${colors.bar}`} />
                  <span>{colors.label}: {pct.toFixed(1)}%</span>
                </div>
              );
            })}
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-1 mt-2 text-[11px] text-muted-foreground/60">
            <span>Target: Groq 25-35%, NVIDIA 25-35%, Ollama 30-50%</span>
          </div>
        </div>
      )}
    </div>
  );
}