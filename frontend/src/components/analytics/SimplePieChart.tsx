"use client";

import { cn } from "@/lib/utils";

interface PieChartProps {
  data: { label: string; value: number; color: string }[];
  size?: number;
  className?: string;
}

export function PieChart({ data, size = 80, className }: PieChartProps) {
  const total = data.reduce((a, b) => a + b.value, 0) || 1;
  let cumulative = 0;
  const segments = data.map((d) => {
    const start = cumulative;
    cumulative += (d.value / total) * 360;
    return { ...d, start, end: cumulative };
  });

  const cx = 50;
  const cy = 50;
  const r = 40;

  function describeArc(s: number, e: number) {
    const x1 = cx + r * Math.cos((s * Math.PI) / 180);
    const y1 = cy + r * Math.sin((s * Math.PI) / 180);
    const x2 = cx + r * Math.cos((e * Math.PI) / 180);
    const y2 = cy + r * Math.sin((e * Math.PI) / 180);
    const large = e - s > 180 ? 1 : 0;
    return `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`;
  }

  return (
    <div className={cn("flex items-center gap-4", className)}>
      <svg width={size} height={size} viewBox="0 0 100 100" className="shrink-0">
        {segments.map((s, i) => (
          <path key={i} d={describeArc(s.start, s.end)} fill={s.color} opacity={0.8} />
        ))}
        <circle cx={cx} cy={cy} r={22} fill="#0f172a" />
      </svg>
      <div className="space-y-1">
        {data.map((d, i) => (
          <div key={i} className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: d.color }} />
            <span className="text-[10px] text-muted-foreground">{d.label}</span>
            <span className="text-[10px] font-medium text-foreground">{Math.round((d.value / total) * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
