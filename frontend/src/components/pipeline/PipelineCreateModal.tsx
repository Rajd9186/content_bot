"use client";

import { useState } from "react";
import { Modal } from "@/components/common/Modal";
import { usePipelineStore } from "@/store/pipeline-store";
import { useUIStore } from "@/store/ui-store";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function PipelineCreateModal({ open, onClose }: Props) {
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("general");
  const [tone, setTone] = useState("professional");
  const [goals, setGoals] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const create = usePipelineStore((s) => s.create);
  const run = usePipelineStore((s) => s.run);
  const setSection = useUIStore((s) => s.setSection);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || submitting) return;
    setSubmitting(true);
    try {
      const id = await create(topic.trim(), audience, tone, goals);
      await run(id);
      onClose();
      setSection("pipeline");
    } catch {
      // error handled by store
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="New Pipeline">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1 block">Topic *</label>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., AI in Healthcare, Climate Change Analysis..."
            className="w-full px-3 py-2 rounded-xl bg-secondary/60 border border-border text-sm text-foreground focus:outline-none focus:border-violet-500"
            required
            autoFocus
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Tone</label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-secondary/60 border border-border text-sm text-foreground focus:outline-none focus:border-violet-500"
            >
              <option value="professional">Professional</option>
              <option value="academic">Academic</option>
              <option value="conversational">Conversational</option>
              <option value="persuasive">Persuasive</option>
              <option value="informative">Informative</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-1 block">Audience</label>
            <select
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-secondary/60 border border-border text-sm text-foreground focus:outline-none focus:border-violet-500"
            >
              <option value="general">General</option>
              <option value="developers">Developers</option>
              <option value="researchers">Researchers</option>
              <option value="executives">Executives</option>
              <option value="technical">Technical</option>
            </select>
          </div>
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1 block">Goals</label>
          <textarea
            value={goals}
            onChange={(e) => setGoals(e.target.value)}
            placeholder="Optional: specific goals or instructions..."
            rows={3}
            className="w-full px-3 py-2 rounded-xl bg-secondary/60 border border-border text-sm text-foreground focus:outline-none focus:border-violet-500 resize-none"
          />
        </div>
        <div className="flex items-center gap-2 pt-2">
          <button
            type="submit"
            disabled={!topic.trim() || submitting}
            className="flex-1 rounded-xl bg-gradient-to-r from-violet-500 to-violet-600 px-4 py-2.5 text-sm font-semibold text-white hover:from-violet-400 hover:to-violet-500 transition-all btn-press disabled:opacity-50"
          >
            {submitting ? "Starting..." : "Create & Start Pipeline"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-secondary/60 px-4 py-2.5 text-sm font-medium text-muted-foreground hover:bg-secondary transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </Modal>
  );
}
