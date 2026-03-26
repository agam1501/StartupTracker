"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { RoundTypeDistribution } from "@/lib/types";

const COLORS = [
  "#8b5cf6", "#22c55e", "#3b82f6", "#6366f1", "#f97316", "#ef4444",
  "#eab308", "#06b6d4", "#ec4899",
];

export function RoundTypeChart({ data }: { data: RoundTypeDistribution[] }) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No data</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="round_type"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label={({ name, value }) => `${name}: ${value}`}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
