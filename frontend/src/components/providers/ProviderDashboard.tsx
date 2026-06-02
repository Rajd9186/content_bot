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

const PROVIDER_COLORS: Record<string, { border: string; bg: string; label: string }> = {
  groq: { border: 'border-emerald-700', bg: 'bg-emerald-900/10', label: 'Groq' },
  nvidia: { border: 'border-blue-700', bg: 'bg-blue-900/10', label: 'NVIDIA' },
  openai: { border: 'border-purple-700', bg: 'bg-purple-900/10', label: 'OpenAI' },
  ollama: { border: 'border-orange-700', bg: 'bg-orange-900/10', label: 'Ollama' },
  anthropic: { border: 'border-yellow-700', bg: 'bg-yellow-900/10', label: 'Anthropic' },
};

function CircuitBadge({ state }: { state: string }) {
  const colors = {
    closed: 'bg-emerald-900/30 text-emerald-400 border-emerald-700',
    half_open: 'bg-yellow-900/30 text-yellow-400 border-yellow-700',
    open: 'bg-red-900/30 text-red-400 border-red-700',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${colors[state as keyof typeof colors] || colors.closed}`}>
      {state.toUpperCase()}
    </span>
  );
}

function UsageBar({ used, limit, label, unit }: { used: number; limit: number; label: string; unit: string }) {
  const pct = limit > 0 ? Math.min(100, (used / limit) * 100) : 0;
  const color = pct > 80 ? 'bg-red-500' : pct > 50 ? 'bg-yellow-500' : 'bg-emerald-500';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-400">
        <span>{label}: {used.toLocaleString()} / {limit.toLocaleString()} {unit}</span>
        <span className={pct > 80 ? 'text-red-400' : pct > 50 ? 'text-yellow-400' : 'text-emerald-400'}>
          {pct.toFixed(0)}%
        </span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
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
      // ignore
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
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Gauge className="w-5 h-5 text-emerald-400" />
          <h2 className="text-xl font-bold text-white">Provider Operations</h2>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-xs text-gray-500">
              Updated {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={loadStats}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 rounded border border-gray-700 text-gray-300 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            Refresh
          </button>
        </div>
      </div>

      {loading && Object.keys(stats).length === 0 && (
        <div className="flex items-center justify-center py-16">
          <div className="text-gray-500">Loading provider statistics...</div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {Object.entries(stats).map(([key, stat]) => {
          const colors = PROVIDER_COLORS[key] || { border: 'border-gray-700', bg: 'bg-gray-900/10', label: key };
          return (
            <div key={key} className={`rounded-lg border ${colors.border} ${colors.bg} p-4 space-y-4`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-base font-semibold text-white">{colors.label}</span>
                  <CircuitBadge state={stat.circuit_state || 'closed'} />
                </div>
                <Activity className="w-4 h-4 text-gray-500" />
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex items-center gap-1.5 text-gray-300">
                  <Zap className="w-3 h-3 text-gray-500" />
                  <span>Active: <strong className="text-white">{stat.active_requests}</strong></span>
                </div>
                <div className="flex items-center gap-1.5 text-gray-300">
                  <Clock className="w-3 h-3 text-gray-500" />
                  <span>Latency: <strong className="text-white">{(stat.average_latency || 0).toFixed(0)}ms</strong></span>
                </div>
                <div className="flex items-center gap-1.5 text-gray-300">
                  {stat.success_rate >= 0.95 ? (
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-3 h-3 text-yellow-400" />
                  )}
                  <span>Success: <strong className="text-white">{(stat.success_rate * 100).toFixed(1)}%</strong></span>
                </div>
                <div className="flex items-center gap-1.5 text-gray-300">
                  <Activity className="w-3 h-3 text-gray-500" />
                  <span>Calls: <strong className="text-white">{(stat.total_calls || 0).toLocaleString()}</strong></span>
                </div>
              </div>

              <UsageBar used={stat.rpm_used} limit={stat.rpm_limit} label="RPM" unit="" />
              <UsageBar used={stat.tpm_used} limit={stat.tpm_limit} label="TPM" unit="" />
            </div>
          );
        })}
      </div>

      {totalCalls > 0 && (
        <div className="rounded-lg border border-gray-700 bg-gray-900/10 p-4">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Request Distribution</h3>
          <div className="flex h-3 rounded-full overflow-hidden bg-gray-800 gap-0.5">
            {Object.entries(stats).map(([key, stat]) => {
              const pct = totalCalls > 0 ? ((stat.total_calls || 0) / totalCalls) * 100 : 0;
              if (pct < 1) return null;
              const color =
                key === 'groq' ? 'bg-emerald-500' :
                key === 'nvidia' ? 'bg-blue-500' :
                key === 'ollama' ? 'bg-orange-500' :
                key === 'openai' ? 'bg-purple-500' :
                'bg-yellow-500';
              return <div key={key} className={`${color} transition-all`} style={{ width: `${pct}%` }} />;
            })}
          </div>
          <div className="flex flex-wrap gap-4 mt-3 text-xs text-gray-400">
            {Object.entries(stats).map(([key, stat]) => {
              const pct = totalCalls > 0 ? ((stat.total_calls || 0) / totalCalls) * 100 : 0;
              const colors = PROVIDER_COLORS[key] || { label: key };
              return (
                <div key={key} className="flex items-center gap-1.5">
                  <div className={`w-2 h-2 rounded-full ${
                    key === 'groq' ? 'bg-emerald-500' :
                    key === 'nvidia' ? 'bg-blue-500' :
                    key === 'ollama' ? 'bg-orange-500' :
                    key === 'openai' ? 'bg-purple-500' :
                    'bg-yellow-500'
                  }`} />
                  <span>{colors.label}: {pct.toFixed(1)}%</span>
                </div>
              );
            })}
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-1 mt-2 text-xs text-gray-500">
            <span>Target: Groq 25-35%, NVIDIA 25-35%, Ollama 30-50%</span>
          </div>
        </div>
      )}
    </div>
  );
}