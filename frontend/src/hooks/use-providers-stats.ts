"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { ProvidersStatsResponse } from "@/types/api";

const REFRESH_INTERVAL = 10000;

export function useProvidersStats() {
  const [stats, setStats] = useState<ProvidersStatsResponse>({});
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const load = async () => {
    try {
      const data = await apiGet<ProvidersStatsResponse>("/providers/stats");
      setStats(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  return { stats, loading, lastRefresh, refresh: load };
}