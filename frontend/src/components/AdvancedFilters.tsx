"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronDown, ChevronUp, X } from "lucide-react";

export default function AdvancedFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [open, setOpen] = useState(
    !!(
      searchParams.get("min_amount") ||
      searchParams.get("max_amount") ||
      searchParams.get("date_from") ||
      searchParams.get("date_to")
    ),
  );

  const [dateFrom, setDateFrom] = useState(searchParams.get("date_from") || "");
  const [dateTo, setDateTo] = useState(searchParams.get("date_to") || "");
  const [minAmount, setMinAmount] = useState(searchParams.get("min_amount") || "");
  const [maxAmount, setMaxAmount] = useState(searchParams.get("max_amount") || "");

  function apply() {
    const params = new URLSearchParams(searchParams.toString());
    if (dateFrom) params.set("date_from", dateFrom);
    else params.delete("date_from");
    if (dateTo) params.set("date_to", dateTo);
    else params.delete("date_to");
    if (minAmount) params.set("min_amount", minAmount);
    else params.delete("min_amount");
    if (maxAmount) params.set("max_amount", maxAmount);
    else params.delete("max_amount");
    params.delete("page");
    router.push(`/funding-rounds?${params.toString()}`);
  }

  function clear() {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("date_from");
    params.delete("date_to");
    params.delete("min_amount");
    params.delete("max_amount");
    params.delete("page");
    setDateFrom("");
    setDateTo("");
    setMinAmount("");
    setMaxAmount("");
    router.push(`/funding-rounds?${params.toString()}`);
  }

  const hasFilters = dateFrom || dateTo || minAmount || maxAmount;

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        <span className="flex items-center gap-2">
          Advanced Filters
          {hasFilters && (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
              Active
            </span>
          )}
        </span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-gray-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-400" />
        )}
      </button>

      {open && (
        <div className="border-t border-gray-200 p-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Date From
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Date To
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Min Amount ($)
              </label>
              <input
                type="number"
                value={minAmount}
                onChange={(e) => setMinAmount(e.target.value)}
                placeholder="0"
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Max Amount ($)
              </label>
              <input
                type="number"
                value={maxAmount}
                onChange={(e) => setMaxAmount(e.target.value)}
                placeholder="No limit"
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={apply}
              className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              Apply
            </button>
            {hasFilters && (
              <button
                onClick={clear}
                className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
              >
                <X className="h-3.5 w-3.5" />
                Clear
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
