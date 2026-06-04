"use client";

import { useEffect, useState, memo } from "react";
import {
  Activity, AlertCircle, ArrowDown, ArrowUp, BarChart3, CheckCircle2,
  ChevronDown, Clock, Cpu, Gauge, RefreshCw, TrendingDown, TrendingUp,
  Wifi, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";

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
  total_failures?: number;
  uptime_ratio?: number;
}

const PROVIDER_CONFIG: Record<string, {
  border: string; bg: string; bar: string; label: string; accent: string; gradient: string
}> = {
  groq: { border: "border-emerald-500/20", bg: "bg-emerald-500/5", bar: "bg-emerald-500", label: "Groq", accent: "text-emerald-400", gradient: "from-emerald-500/20 to-emerald-500/5" },
  nvidia: { border: "border-blue-500/20", bg: "bg-blue-500/5", bar: "bg-blue-500", label: "NVIDIA", accent: "text-blue-400", gradient: "from-blue-500/20 to-blue-500/5" },
  openai: { border: "border-violet-500/20", bg: "bg-violet-500/5", bar: "bg-violet-500", label: "OpenAI", accent: "text-violet-400", gradient: "from-violet-500/20 to-violet-500/5" },
  ollama: { border: "border-orange-500/20", bg: "bg-orange-500/5", bar: "bg-orange-500", label: "Ollama", accent: "text-orange-400", gradient: "from-orange-500/20 to-orange-500/5" },
  anthropic: { border: "border-amber-500/20", bg: "bg-amber-500/5", bar: "bg-amber-500", label: "Anthropic", accent: "text-amber-400", gradient: "from-amber-500/20 to-amber-500/5" },
};

function CircuitBadge({ state }: { state: string }) {
  const config = {
    closed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    half_open: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    open: "bg-red-500/10 text-red-400 border-red-500/20",
  }[state] || "bg-secondary text-muted-foreground border-border";

  const icon = state === "closed" ? <CheckCircle2 className="h-2.5 w-2.5" />
    : state === "half_open" ? <AlertCircle className="h-2.5 w-2.5" />
    : <AlertCircle className="h-2.5 w-2.5" />;

  return (
    <span className={cn("flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border font-medium", config)}>
      {icon}
      {state.toUpperCase()}
    </span>
  );
}

function MetricCard({ icon, label, value, sub, accent = "text-violet-400" }: {
  icon: React.ReactNode; label: string; value: string; sub?: string; accent?: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <div className={cn("flex h-7 w-7 items-center justify-center rounded-lg bg-secondary/60 shrink-0", accent.includes("emerald") && "text-emerald-400", accent.includes("blue") && "text-blue-400", !accent.includes("emerald") && !accent.includes("blue") && "text-muted-foreground")}>
        {icon}
      </div>
      <div>
        <div className="text-[11px] font-semibold text-foreground">{value}</div>
        <div className="text-[9px] text-muted-foreground">{label}{sub && <span className="ml-1">{sub}</span>}</div>
      </div>
    </div>
  );
}

function UsageBar({ used, limit, label, color }: { used: number; limit: number; label: string; color: string }) {
  const pct = limit > 0 ? Math.min(100, (used / limit) * 100) : 0;
  const barColor = pct > 80 ? "bg-red-500" : pct > 50 ? "bg-amber-500" : `bg-${color}`;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>{label}</span>
        <span className={pct > 80 ? "text-red-400" : pct > 50 ? "text-amber-400" : "text-foreground"}>
          {used.toLocaleString()}/{limit.toLocaleString()}
        </span>
      </div>
      <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all duration-500", barColor)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

const ProviderCard = memo(function ProviderCard({ name, stat }: { name: string; stat: ProviderStats }) {
  const config = PROVIDER_CONFIG[name] || {
    border: "border-border", bg: "bg-card/40", bar: "bg-violet-500", label: name, accent: "text-violet-400", gradient: "from-secondary/20 to-secondary/5"
  };

  const successPct = (stat.success_rate * 100).toFixed(1);
  const latency = stat.average_latency?.toFixed(0) ?? "—";
  const rpmPct = stat.rpm_limit > 0 ? Math.min(100, (stat.rpm_used / stat.rpm_limit) * 100) : 0;
  const tpmPct = stat.tpm_limit > 0 ? Math.min(100, (stat.tpm_used / stat.tpm_limit) * 100) : 0;

  const getSuccessColor = (rate: number) => {
    if (rate >= 0.95) return "text-emerald-400";
    if (rate >= 0.8) return "text-amber-400";
    return "text-red-400";
  };

  const getLatencyTrend = (ms: number) => {
    if (ms < 500) return <ArrowDown className="h-3 w-3 text-emerald-400" />;
    if (ms < 1500) return null;
    return <ArrowUp className="h-3 w-3 text-amber-400" />;
  };

  return (
    <div className={cn("group relative overflow-hidden rounded-2xl border bg-gradient-to-br p-4 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg", config.border, config.gradient)}>
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-black/5 to-transparent" />

      <div className="relative space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-foreground">{config.label}</h3>
              <CircuitBadge state={stat.circuit_state || "closed"} />
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className={cn(
                "h-2 w-2 rounded-full",
                stat.circuit_state === "open" ? "bg-red-400 animate-pulse"
                  : stat.circuit_state === "half_open" ? "bg-amber-400 animate-pulse"
                  : "bg-emerald-400"
              )} />
              <span className="text-[10px] text-muted-foreground capitalize">
                {stat.circuit_state === "closed" ? "Healthy" : stat.circuit_state === "half_open" ? "Degraded" : "Down"}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className={cn("text-lg font-bold", config.accent)}>{successPct}%</div>
            <div className="text-[9px] text-muted-foreground">success rate</div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="rounded-xl bg-secondary/40 p-2 text-center">
            <div className="flex items-center justify-center gap-0.5">
              {getLatencyTrend(stat.average_latency)}
              <span className="text-[13px] font-bold text-foreground">{latency}</span>
            </div>
            <div className="text-[9px] text-muted-foreground mt-0.5">Latency (ms)</div>
          </div>
          <div className="rounded-xl bg-secondary/40 p-2 text-center">
            <div className="text-[13px] font-bold text-foreground">{stat.active_requests ?? 0}</div>
            <div className="text-[9px] text-muted-foreground mt-0.5">Active</div>
          </div>
          <div className="rounded-xl bg-secondary/40 p-2 text-center">
            <div className="text-[13px] font-bold text-foreground">{stat.queue_length ?? 0}</div>
            <div className="text-[9px] text-muted-foreground mt-0.5">Queue</div>
          </div>
          <div className="rounded-xl bg-secondary/40 p-2 text-center">
            <div className="text-[13px] font-bold text-red-400">{(stat.total_failures ?? 0).toLocaleString()}</div>
            <div className="text-[9px] text-muted-foreground mt-0.5">Failures</div>
          </div>
        </div>

        <div className="space-y-2">
          <UsageBar used={stat.rpm_used} limit={stat.rpm_limit} label="RPM" color="violet-500" />
          <UsageBar used={stat.tpm_used} limit={stat.tpm_limit} label="TPM" color="blue-500" />
        </div>

        <div className="flex items-center justify-between text-[10px] text-muted-foreground border-t border-border/40 pt-3">
          <span>{(stat.total_calls ?? 0).toLocaleString()} total calls</span>
          <span>{rpmPct.toFixed(0)}% RPM · {tpmPct.toFixed(0)}% TPM</span>
        </div>
      </div>
    </div>
  );
});

export function ProviderDashboard() {
  const [stats, setStats] = useState<Record<string, ProviderStats>>({});
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [sortBy, setSortBy] = useState<"success" | "latency" | "calls" | "active">("success");

  const loadStats = async () => {
    try {
      const res = await fetch("/api/providers/stats");
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch {} finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  };

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const providers = Object.entries(stats);

  const sortedProviders = [...providers].sort(([aKey, aStat], [bKey, bStat]) => {
    switch (sortBy) {
      case "success": return bStat.success_rate - aStat.success_rate;
      case "latency": return aStat.average_latency - bStat.average_latency;
      case "calls": return bStat.total_calls - aStat.total_calls;
      case "active": return bStat.active_requests - aStat.active_requests;
      default: return 0;
    }
  });

  const totalCalls = providers.reduce((s, [, p]) => s + (p.total_calls || 0), 0);
  const totalActive = providers.reduce((s, [, p]) => s + (p.active_requests || 0), 0);
  const totalQueue = providers.reduce((s, [, p]) => s + (p.queue_length || 0), 0);
  const avgSuccess = providers.length > 0
    ? (providers.reduce((s, [, p]) => s + p.success_rate, 0) / providers.length * 100).toFixed(1)
    : "—";
  const avgLatency = providers.length > 0
    ? (providers.reduce((s, [, p]) => s + p.average_latency, 0) / providers.length).toFixed(0)
    : "—";
  const worstCircuit = providers.some(([, p]) => p.circuit_state === "open") ? "open"
    : providers.some(([, p]) => p.circuit_state === "half_open") ? "degraded" : "healthy";

  return (
    <div className="space-y-6 p-1">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/20 to-violet-600/10 border border-violet-500/20 shadow-lg shadow-violet-500/10">
            <Gauge className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-foreground">Provider Operations</h2>
            <p className="text-[10px] text-muted-foreground">
              {providers.length} providers · Updated {lastRefresh?.toLocaleTimeString() ?? "—"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 bg-secondary/60 border border-border rounded-xl px-3 py-1.5">
            <span className="text-[10px] text-muted-foreground">Sort:</span>
            {(["success", "latency", "calls", "active"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setSortBy(s)}
                className={cn(
                  "px-2 py-0.5 rounded text-[10px] font-medium transition-colors capitalize",
                  sortBy === s ? "bg-violet-500/20 text-violet-400" : "text-muted-foreground hover:text-foreground"
                )}
              >
                {s}
              </button>
            ))}
          </div>
          <button
            onClick={loadStats}
            className="btn-press flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-secondary hover:bg-secondary/80 text-foreground rounded-xl border border-border transition-all"
          >
            <RefreshCw className={cn("w-3 h-3", loading && "animate-spin")} />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn(
              "h-2 w-2 rounded-full",
              worstCircuit === "healthy" ? "bg-emerald-400" : worstCircuit === "degraded" ? "bg-amber-400 animate-pulse" : "bg-red-400 animate-pulse"
            )} />
            <span className="text-[10px] font-medium text-muted-foreground">System Status</span>
          </div>
          <div className="text-lg font-bold text-foreground capitalize">{worstCircuit}</div>
        </div>

        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <Wifi className="h-3 w-3 text-violet-400" />
            <span className="text-[10px] font-medium text-muted-foreground">Active Requests</span>
          </div>
          <div className="text-lg font-bold text-foreground">{totalActive.toLocaleString()}</div>
        </div>

        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <Activity className="h-3 w-3 text-amber-400" />
            <span className="text-[10px] font-medium text-muted-foreground">Queue Depth</span>
          </div>
          <div className="text-lg font-bold text-foreground">{totalQueue.toLocaleString()}</div>
        </div>

        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="h-3 w-3 text-blue-400" />
            <span className="text-[10px] font-medium text-muted-foreground">Avg Latency</span>
          </div>
          <div className="text-lg font-bold text-foreground">{avgLatency}ms</div>
        </div>

        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 className="h-3 w-3 text-emerald-400" />
            <span className="text-[10px] font-medium text-muted-foreground">Avg Success</span>
          </div>
          <div className="text-lg font-bold text-foreground">{avgSuccess}%</div>
        </div>

        <div className="rounded-2xl border border-border bg-card/40 p-3">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="h-3 w-3 text-orange-400" />
            <span className="text-[10px] font-medium text-muted-foreground">Total Calls</span>
          </div>
          <div className="text-lg font-bold text-foreground">{totalCalls.toLocaleString()}</div>
        </div>
      </div>

      {loading && providers.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 skeleton rounded-2xl" />
          ))}
        </div>
      ) : providers.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center rounded-2xl border border-dashed border-border">
          <Gauge className="h-12 w-12 text-muted-foreground/20 mb-4" />
          <h3 className="text-sm font-semibold text-foreground mb-1">No providers configured</h3>
          <p className="text-xs text-muted-foreground">Configure LLM providers in your backend settings</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedProviders.map(([key, stat]) => (
            <ProviderCard key={key} name={key} stat={stat as ProviderStats} />
          ))}
        </div>
      )}

      {totalCalls > 0 && (
        <div className="rounded-2xl border border-border bg-card/40 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-violet-400" />
              Request Distribution
            </h3>
            <span className="text-[10px] text-muted-foreground">Target: Groq 25-35% · NVIDIA 25-35% · Ollama 30-50%</span>
          </div>
          <div className="flex h-4 rounded-full overflow-hidden bg-secondary gap-0.5">
            {providers.map(([key, stat]) => {
              const pct = totalCalls > 0 ? ((stat.total_calls || 0) / totalCalls) * 100 : 0;
              if (pct < 1) return null;
              const barColor = PROVIDER_CONFIG[key]?.bar || "bg-violet-500";
              return (
                <div
                  key={key}
                  className={cn("h-full transition-all rounded-full", barColor)}
                  style={{ width: `${pct}%` }}
                  title={`${PROVIDER_CONFIG[key]?.label || key}: ${pct.toFixed(1)}%`}
                />
              );
            })}
          </div>
          <div className="flex flex-wrap gap-4 mt-3">
            {providers.map(([key, stat]) => {
              const pct = totalCalls > 0 ? ((stat.total_calls || 0) / totalCalls) * 100 : 0;
              const config = PROVIDER_CONFIG[key] || { bar: "bg-violet-500", label: key, accent: "text-violet-400" };
              return (
                <div key={key} className="flex items-center gap-2">
                  <div className={cn("w-2.5 h-2.5 rounded-full", config.bar)} />
                  <div>
                    <span className={cn("text-[11px] font-medium", config.accent)}>{config.label}</span>
                    <span className="text-[10px] text-muted-foreground ml-1.5">
                      {pct.toFixed(1)}% · {(stat.total_calls || 0).toLocaleString()} calls
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}