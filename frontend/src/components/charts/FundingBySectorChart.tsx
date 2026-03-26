"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { FundingBySector } from "@/lib/types";

const COLORS = [
  "#8b5cf6", "#10b981", "#f43f5e", "#3b82f6", "#f97316",
  "#22c55e", "#ef4444", "#eab308", "#f59e0b", "#06b6d4",
  "#ec4899", "#84cc16", "#64748b", "#6366f1", "#9ca3af",
];

function formatAmount(value: number): string {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value}`;
}

export function FundingBySectorChart({ data }: { data: FundingBySector[] }) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No data</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20 }}>
        <XAxis type="number" tickFormatter={formatAmount} />
        <YAxis
          type="category"
          dataKey="sector"
          width={140}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          formatter={(value) => [formatAmount(Number(value)), "Total Funding"]}
        />
        <Bar dataKey="total_amount" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
