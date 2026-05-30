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
        <div className="rounded-lg border border-border bg-black/20 p-3">
          <p className="text-xs text-foreground">
            {draftContent.slice(0, 300)}
            {draftContent.length > 300 ? "..." : ""}
          </p>
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-medium text-muted-foreground">Feedback (optional)</label>
          <input
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Enter feedback..."
            className="w-full rounded-lg border border-border bg-black/20 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/40 focus:border-emerald-500/50 focus:outline-none focus:ring-1 focus:ring-emerald-500/20"
          />
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => handleAction(false)}
            className="flex-1 rounded-lg border border-red-500/30 py-2 text-sm font-medium text-red-300 hover:bg-red-500/10 transition-colors"
          >
            Reject
          </button>
          <button
            onClick={() => handleAction(true)}
            className="flex-1 rounded-lg bg-emerald-500 py-2 text-sm font-medium text-white shadow-lg shadow-emerald-500/20 hover:bg-emerald-600 transition-all"
          >
            Approve
          </button>
        </div>
      </div>
    </Modal>
  );
}
