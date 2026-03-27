"use client";

import { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { getFundingByMonth } from "@/lib/api";
import type { FundingByMonth } from "@/lib/types";

const SECTORS = [
  "AI/ML", "Climate/Energy", "Crypto/Web3", "Cybersecurity",
  "E-Commerce/Retail", "EdTech", "Fintech", "Food/Agriculture",
  "Hardware/Robotics", "Healthcare/Biotech", "Media/Entertainment",
  "Real Estate/PropTech", "SaaS/Enterprise", "Transportation/Logistics", "Other",
];

function formatAmount(value: number): string {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value}`;
}

function formatMonth(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

export function FundingTrendsChart({
  initialData,
}: {
  initialData: FundingByMonth[];
}) {
  const [data, setData] = useState(initialData);
  const [sector, setSector] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSectorChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const val = e.target.value;
    setSector(val);
    setLoading(true);
    try {
      const result = await getFundingByMonth({
        sector: val || undefined,
        months: 12,
      });
      setData(result);
    } catch {
      // keep existing data on error
    } finally {
      setLoading(false);
    }
  }

  if (data.length === 0 && !loading) {
    return <p className="py-8 text-center text-sm text-gray-400">No data</p>;
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-end">
        <select
          value={sector}
          onChange={handleSectorChange}
          disabled={loading}
          className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Sectors</option>
          {SECTORS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={data} margin={{ left: 10, right: 10, top: 5 }}>
          <defs>
            <linearGradient id="fundingGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="month"
            tickFormatter={formatMonth}
            tick={{ fontSize: 12 }}
          />
          <YAxis tickFormatter={formatAmount} tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value) => [formatAmount(Number(value)), "Total Funding"]}
            labelFormatter={(label) => formatMonth(String(label))}
          />
          <Area
            type="monotone"
            dataKey="total_amount"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#fundingGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
