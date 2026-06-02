"use client";

import React, { useState } from 'react';
import { Modal } from '@/components/common/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/common/Badge';

interface ContextPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  onAccept: (selectedIds: string[]) => void;
  retrievedMemories: any[];
  pinnedKnowledge: any[];
}

export default function ContextPreview({ 
  isOpen, 
  onClose, 
  onAccept, 
  retrievedMemories, 
  pinnedKnowledge 
}: ContextPreviewProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const toggleMemory = (id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      title="Intelligence Context Preview"
    >
      <div className="space-y-6 max-w-2xl">
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            The system has retrieved the following knowledge from your project history to augment this generation.
          </p>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-semibold uppercase text-gray-500">Pinned Knowledge (Always Included)</h3>
          <div className="space-y-2">
            {pinnedKnowledge.map((k, i) => (
              <div key={i} className="p-3 rounded-lg border bg-card flex justify-between items-center">
                <p className="text-sm">{k.content}</p>
                <Badge variant="outline" className="bg-yellow-100 text-yellow-800 border-yellow-300">Pinned</Badge>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-semibold uppercase text-gray-500">Retrieved Memories (Select to Include)</h3>
          <div className="space-y-2">
            {retrievedMemories.map((m, i) => (
              <div 
                key={i} 
                onClick={() => toggleMemory(m.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedIds.includes(m.id) ? 'border-primary bg-primary/5' : 'bg-card'
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <Badge variant="secondary" className="text-[10px]">{m.memory_type}</Badge>
                  <span className="text-xs text-gray-400">Score: {m.score.toFixed(2)}</span>
                </div>
                <p className="text-sm">{m.content}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-6 border-t">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={() => onAccept(selectedIds)}>Accept & Generate</Button>
        </div>
      </div>
    </Modal>
  );
}
