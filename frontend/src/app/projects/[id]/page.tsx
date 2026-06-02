"use client";

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useApi } from '@/hooks/use-api';
import { Badge } from '@/components/common/Badge';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { MetricsCard } from '@/components/analytics/MetricsCard';
import { StatsGrid } from '@/components/analytics/StatsGrid';

export default function ProjectDashboardPage() {
  const { id } = useParams();
  const { get, post } = useApi();
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const data = await get(`/api/projects/${id}/dashboard`);
        setDashboard(data);
      } catch (error) {
        console.error("Failed to fetch dashboard", error);
      } finally {
        setLoading(false);
      }
    }
    fetchDashboard();
  }, [id]);

  if (loading) return <div className="flex h-full items-center justify-center"><LoadingSpinner /></div>;
  if (!dashboard) return <div className="p-8 text-center">Project not found</div>;

  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">{dashboard.name}</h1>
          <p className="text-gray-500">Project Intelligence Dashboard</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline">Active</Badge>
        </div>
      </div>

      <StatsGrid>
        <MetricsCard 
          title="Total Memories" 
          value={dashboard.total_memories.toString()} 
          description="Semantic knowledge fragments" 
        />
        <MetricsCard 
          title="Total Outputs" 
          value={dashboard.total_outputs.toString()} 
          description="Generated assets" 
        />
        <MetricsCard 
          title="Token Usage" 
          value={dashboard.total_tokens.toLocaleString()} 
          description="Cumulative cost" 
        />
        <MetricsCard 
          title="Last Activity" 
          value={new Date(dashboard.last_activity).toLocaleDateString()} 
          description="Recent update" 
        />
      </StatsGrid>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-card p-6 rounded-xl border">
          <h2 className="text-xl font-semibold mb-4">Knowledge Distribution</h2>
          <div className="h-64 flex items-center justify-center text-gray-400 italic">
            Memory distribution chart coming soon...
          </div>
        </div>
        <div className="bg-card p-6 rounded-xl border">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {/* Mock activity list */}
            {[1,2,3].map(i => (
              <div key={i} className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent transition-colors cursor-pointer">
                <div className="w-2 h-2 rounded-full bg-primary" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Generated article: "Industry Trends 2026"</p>
                  <p className="text-xs text-gray-500">2 hours ago</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
