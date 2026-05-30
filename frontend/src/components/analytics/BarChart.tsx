"use client";

import { cn } from "@/lib/utils";

interface BarChartProps {
  data: { label: string; value: number; color?: string }[];
  height?: number;
  className?: string;
}

export function BarChart({ data, height = 120, className }: BarChartProps) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className={cn("flex items-end gap-1", className)} style={{ height }}>
      {data.map((d, i) => (
        <div key={i} className="flex flex-1 flex-col items-center gap-1">
          <span className="text-[9px] text-muted-foreground/60">{d.value}</span>
          <div
            className="w-full rounded-t transition-all duration-500"
            style={{
              height: `${(d.value / max) * 100}%`,
              backgroundColor: d.color ?? "rgba(16,185,129,0.5)",
              minHeight: 2,
            }}
          />
          <span className="text-[8px] text-muted-foreground/40 truncate w-full text-center">{d.label}</span>
        </div>
      ))}
    </div>
  );
}
