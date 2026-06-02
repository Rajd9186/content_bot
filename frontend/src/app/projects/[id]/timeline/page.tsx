"use client";

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useApi } from '@/hooks/use-api';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Badge } from '@/components/common/Badge';

interface TimelineEvent {
  type: string;
  timestamp: string;
  content: string;
  status: string;
}

export default function ProjectTimeline() {
  const { id } = useParams();
  const { get } = useApi();
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTimeline() {
      try {
        // This would typically be a specific timeline endpoint, 
        // but we can aggregate from project outputs/conversations
        const data = await get(`/api/projects/${id}/outputs`); 
        setEvents(data.map((o: any) => ({
          type: 'output',
          timestamp: o.created_at,
          content: o.title,
          status: 'completed'
        })));
      } catch (error) {
        console.error("Timeline fetch failed", error);
      } finally {
        setLoading(false);
      }
    }
    fetchTimeline();
  }, [id]);

  if (loading) return <div className="flex h-full items-center justify-center"><LoadingSpinner /></div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-8">Project Timeline</h1>
      
      <div className="relative border-l-2 border-gray-200 ml-4 space-y-8">
        {events.map((event, idx) => (
          <div key={idx} className="relative pl-8">
            <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-primary border-2 border-white" />
            <div className="flex justify-between items-start mb-1">
              <span className="text-xs font-medium text-gray-500 uppercase">
                {event.type} • {new Date(event.timestamp).toLocaleString()}
              </span>
              <Badge variant="outline">{event.status}</Badge>
            </div>
            <div className="p-4 rounded-lg bg-card border hover:border-primary transition-colors cursor-pointer">
              <p className="font-medium">{event.content}</p>
            </div>
          </div>
        ))}
        {events.length === 0 && (
          <div className="text-center py-20 text-gray-500">
            No timeline events found for this project.
          </div>
        )}
      </div>
    </div>
  );
}
