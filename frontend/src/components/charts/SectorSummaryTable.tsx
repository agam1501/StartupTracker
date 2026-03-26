"use client";

import type { SectorSummary } from "@/lib/types";

function formatAmount(value: number): string {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

export function SectorSummaryTable({ data }: { data: SectorSummary[] }) {
  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-400">No data</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead>
          <tr className="bg-gray-50/50">
            <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              Sector
            </th>
            <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
              Companies
            </th>
            <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
              Rounds
            </th>
            <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
              Total Funding
            </th>
            <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
              Avg Round
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {data.map((row) => (
            <tr key={row.sector} className="hover:bg-gray-50/50">
              <td className="whitespace-nowrap px-4 py-2.5 text-sm font-medium text-gray-900">
                {row.sector}
              </td>
              <td className="whitespace-nowrap px-4 py-2.5 text-right text-sm text-gray-600">
                {row.company_count}
              </td>
              <td className="whitespace-nowrap px-4 py-2.5 text-right text-sm text-gray-600">
                {row.round_count}
              </td>
              <td className="whitespace-nowrap px-4 py-2.5 text-right text-sm font-medium text-gray-900">
                {formatAmount(row.total_funding)}
              </td>
              <td className="whitespace-nowrap px-4 py-2.5 text-right text-sm text-gray-600">
                {formatAmount(row.avg_round_size)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
