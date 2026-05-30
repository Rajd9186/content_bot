"use client";

import { cn } from "@/lib/utils";

interface LineChartProps {
  data: { label: string; value: number }[];
  height?: number;
  className?: string;
}

export function LineChart({ data, height = 80, className }: LineChartProps) {
  if (data.length < 2) return null;
  const values = data.map((d) => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values, min + 1);
  const range = max - min;
  const w = 100 / (data.length - 1);

  const points = data.map((d, i) => {
    const x = i * w;
    const y = ((max - d.value) / range) * 100;
    return `${x},${y}`;
  });

  return (
    <div className={cn("relative", className)} style={{ height }}>
      <svg viewBox={`0 0 100 100`} className="h-full w-full overflow-visible" preserveAspectRatio="none">
        <polyline
          points={points.join(" ")}
          fill="none"
          stroke="rgba(16,185,129,0.6)"
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
        />
        <polyline
          points={points.join(" ")}
          fill="none"
          stroke="rgba(16,185,129,0.2)"
          strokeWidth="4"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </div>
  );
}
