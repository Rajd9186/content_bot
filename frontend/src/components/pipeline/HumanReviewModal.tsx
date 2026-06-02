"use client";

import { useState } from "react";
import { usePipelineStore } from "@/store/pipeline-store";
import { Modal } from "@/components/common";

export function HumanReviewModal() {
  const currentId = usePipelineStore((s) => s.currentId);
  const content = usePipelineStore((s) => s.content);
  const review = usePipelineStore((s) => s.review);
  const status = usePipelineStore((s) => s.status);
  const [feedback, setFeedback] = useState("");

  const open = currentId != null && status?.status === "review";

  if (!open) return <></>;

  const handleAction = async (approved: boolean) => {
    await review(currentId!, approved ? "approve" : "reject", feedback || undefined);
    setFeedback("");
  };

  const draftContent = content?.final_content ?? content?.draft_content ?? "";

  return (
    <Modal open={open} onClose={() => {}} title="Human Review Required">
      <div className="space-y-4">
        <div className="rounded-xl border border-border bg-secondary/30 p-3">
          <p className="text-xs text-foreground leading-relaxed">
            {draftContent.slice(0, 300)}
            {draftContent.length > 300 ? "..." : ""}
          </p>
        </div>
        <div>
          <label className="mb-1.5 block text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">Feedback (optional)</label>
          <input
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Enter feedback..."
            className="input-glow w-full rounded-xl border border-border bg-secondary/30 px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:border-violet-500/50 focus:outline-none transition-all"
          />
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => handleAction(false)}
            className="btn-press flex-1 rounded-xl border border-red-500/30 py-2.5 text-sm font-medium text-red-400 hover:bg-red-500/10 transition-all"
          >
            Reject
          </button>
          <button
            onClick={() => handleAction(true)}
            className="btn-press flex-1 rounded-xl bg-gradient-to-r from-violet-600 to-violet-700 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-violet-600 transition-all duration-200"
          >
            Approve
          </button>
        </div>
      </div>
    </Modal>
  );
}