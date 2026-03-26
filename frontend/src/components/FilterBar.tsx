"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { ArrowUpDown, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface FilterOption {
  label: string;
  value: string;
}

interface FilterBarProps {
  basePath: string;
  /** Pill-style filter for a single param (e.g. round_type, sector) */
  pillFilter?: {
    param: string;
    options: FilterOption[];
    label?: string;
  };
  /** Sort options */
  sortOptions?: FilterOption[];
  sortParam?: string;
  /** Preserve these params across navigations */
  preserveParams?: string[];
}

export default function FilterBar({
  basePath,
  pillFilter,
  sortOptions,
  sortParam = "sort_by",
  preserveParams = [],
}: FilterBarProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const buildUrl = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams();

      // Preserve specified params
      const allPreserve = [
        ...preserveParams,
        pillFilter?.param,
        sortParam,
        "sort_order",
        "search",
      ].filter(Boolean) as string[];

      for (const key of allPreserve) {
        const val = searchParams.get(key);
        if (val) params.set(key, val);
      }

      // Apply updates (null = remove)
      for (const [key, val] of Object.entries(updates)) {
        if (val === null) {
          params.delete(key);
        } else {
          params.set(key, val);
        }
      }

      // Always reset to page 1 when filtering
      params.delete("page");

      const qs = params.toString();
      return qs ? `${basePath}?${qs}` : basePath;
    },
    [basePath, searchParams, preserveParams, pillFilter?.param, sortParam],
  );

  const currentPill = pillFilter ? searchParams.get(pillFilter.param) || "" : "";
  const currentSort = searchParams.get(sortParam) || "";
  const currentOrder = searchParams.get("sort_order") || "asc";

  const hasActiveFilters =
    currentPill || currentSort || searchParams.get("sort_order");

  return (
    <div className="flex flex-col gap-3">
      {/* Pill filters */}
      {pillFilter && (
        <div className="flex flex-wrap items-center gap-2">
          {pillFilter.label && (
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider mr-1">
              {pillFilter.label}
            </span>
          )}
          <button
            onClick={() => router.push(buildUrl({ [pillFilter.param]: null }))}
            className={cn(
              "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
              !currentPill
                ? "border-blue-600 bg-blue-50 text-blue-700"
                : "border-gray-200 text-gray-600 hover:bg-gray-50",
            )}
          >
            All
          </button>
          {pillFilter.options.map((opt) => (
            <button
              key={opt.value}
              onClick={() =>
                router.push(buildUrl({ [pillFilter.param]: opt.value }))
              }
              className={cn(
                "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
                currentPill === opt.value
                  ? "border-blue-600 bg-blue-50 text-blue-700"
                  : "border-gray-200 text-gray-600 hover:bg-gray-50",
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {/* Sort controls */}
      {sortOptions && sortOptions.length > 0 && (
        <div className="flex items-center gap-2">
          <ArrowUpDown className="h-3.5 w-3.5 text-gray-400" />
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Sort
          </span>
          {sortOptions.map((opt) => {
            const isActive = currentSort === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() => {
                  if (isActive) {
                    // Toggle order
                    const newOrder = currentOrder === "asc" ? "desc" : "asc";
                    router.push(
                      buildUrl({
                        [sortParam]: opt.value,
                        sort_order: newOrder,
                      }),
                    );
                  } else {
                    router.push(
                      buildUrl({
                        [sortParam]: opt.value,
                        sort_order: "desc",
                      }),
                    );
                  }
                }}
                className={cn(
                  "inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors",
                  isActive
                    ? "border-blue-600 bg-blue-50 text-blue-700"
                    : "border-gray-200 text-gray-600 hover:bg-gray-50",
                )}
              >
                {opt.label}
                {isActive && (
                  <span className="text-[10px]">
                    {currentOrder === "asc" ? "\u2191" : "\u2193"}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Clear all filters */}
      {hasActiveFilters && (
        <button
          onClick={() => {
            const params = new URLSearchParams();
            const search = searchParams.get("search");
            if (search) params.set("search", search);
            const qs = params.toString();
            router.push(qs ? `${basePath}?${qs}` : basePath);
          }}
          className="inline-flex w-fit items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
        >
          <X className="h-3 w-3" />
          Clear filters
        </button>
      )}
    </div>
  );
}
