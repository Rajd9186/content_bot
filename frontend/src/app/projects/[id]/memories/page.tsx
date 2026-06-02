"use client";

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useApi } from '@/hooks/use-api';
import { Badge } from '@/components/common/Badge';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Modal } from '@/components/common/Modal';
import { Input } from '@/components/ui/Input'; // Assuming generic Input exists
import { Button } from '@/components/ui/Button'; // Assuming generic Button exists

interface Memory {
  content: string;
  score: number;
  memory_type: string;
  created_at: string;
}

export default function MemoryExplorer() {
  const { id } = useParams();
  const { get, post, delete: deleteApi } = useApi();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);

  async function handleSearch() {
    setLoading(true);
    try {
      const data = await post(`/api/projects/${id}/memory/search`, { query, limit: 20 });
      setResults(data);
    } catch (error) {
      console.error("Search failed", error);
    } finally {
      setLoading(false);
    }
  }

  async function handlePin(memory: Memory) {
    try {
      // Mocking memory_id as content hash for simplicity if ID is missing in response
      const memoryId = btoa(memory.content).substring(0, 12); 
      await post(`/api/projects/${id}/memory/${memoryId}/pin`, { priority: 1 });
      alert("Memory pinned!");
    } catch (error) {
      console.error("Pinning failed", error);
    }
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Memory Explorer</h1>
        <Badge variant="outline">Semantic Search</Badge>
      </div>

      <div className="flex gap-2">
        <input 
          className="flex-1 p-2 rounded-lg border bg-background"
          placeholder="Search project knowledge..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <Button onClick={handleSearch} disabled={loading}>
          {loading ? <LoadingSpinner /> : "Search"}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.map((mem, idx) => (
          <div 
            key={idx} 
            className="p-4 rounded-xl border bg-card hover:border-primary transition-all cursor-pointer"
            onClick={() => setSelectedMemory(mem)}
          >
            <div className="flex justify-between items-start mb-2">
              <Badge variant="secondary">{mem.memory_type}</Badge>
              <span className="text-xs text-gray-500">Score: {mem.score.toFixed(3)}</span>
            </div>
            <p className="text-sm line-clamp-3 mb-4">{mem.content}</p>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handlePin(mem); }}>
                Pin
              </Button>
            </div>
          </div>
        ))}
        {results.length === 0 && !loading && (
          <div className="col-span-full text-center py-20 text-gray-500">
            No memories found. Try a different query.
          </div>
        )}
      </div>

      <Modal 
        isOpen={!!selectedMemory} 
        onClose={() => setSelectedMemory(null)} 
        title="Memory Detail"
      >
        {selectedMemory && (
          <div className="space-y-4">
            <div className="flex gap-2">
              <Badge>{selectedMemory.memory_type}</Badge>
              <span className="text-xs text-gray-400">{new Date(selectedMemory.created_at).toLocaleString()}</span>
            </div>
            <p className="text-lg leading-relaxed">{selectedMemory.content}</p>
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="destructive" onClick={() => alert("Delete memory logic here")}>
                Delete
              </Button>
              <Button onClick={() => setSelectedMemory(null)}>Close</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
