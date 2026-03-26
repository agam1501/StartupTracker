"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { TopInvestor } from "@/lib/types";

function formatAmount(value: number): string {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value}`;
}

export function TopInvestorsChart({ data }: { data: TopInvestor[] }) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No data</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={data.slice(0, 10)}
        layout="vertical"
        margin={{ left: 20, right: 20 }}
      >
        <XAxis type="number" />
        <YAxis
          type="category"
          dataKey="name"
          width={140}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          formatter={(value, name) => {
            if (name === "deal_count") return [Number(value), "Deals"];
            return [formatAmount(Number(value)), "Total Invested"];
          }}
        />
        <Bar dataKey="deal_count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
