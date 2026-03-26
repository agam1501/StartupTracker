"use client";

import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  basePath: string;
  extraParams?: Record<string, string>;
}

export default function Pagination({
  page,
  pageSize,
  total,
  basePath,
  extraParams = {},
}: PaginationProps) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  function buildHref(p: number) {
    const params = new URLSearchParams(extraParams);
    params.set("page", String(p));
    return `${basePath}?${params.toString()}`;
  }

  // Show up to 5 page numbers centered on current page
  const pages: number[] = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, start + 4);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex items-center justify-between">
      <p className="text-sm text-gray-500">
        Showing {(page - 1) * pageSize + 1}&ndash;
        {Math.min(page * pageSize, total)} of {total}
      </p>
      <div className="flex items-center gap-1">
        {page > 1 ? (
          <Link
            href={buildHref(page - 1)}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-gray-500 transition-colors hover:bg-gray-100"
          >
            <ChevronLeft className="h-4 w-4" />
          </Link>
        ) : (
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-md text-gray-300">
            <ChevronLeft className="h-4 w-4" />
          </span>
        )}

        {pages.map((p) => (
          <Link
            key={p}
            href={buildHref(p)}
            className={cn(
              "inline-flex h-8 w-8 items-center justify-center rounded-md text-sm font-medium transition-colors",
              p === page
                ? "bg-blue-600 text-white"
                : "text-gray-600 hover:bg-gray-100"
            )}
          >
            {p}
          </Link>
        ))}

        {page < totalPages ? (
          <Link
            href={buildHref(page + 1)}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-gray-500 transition-colors hover:bg-gray-100"
          >
            <ChevronRight className="h-4 w-4" />
          </Link>
        ) : (
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-md text-gray-300">
            <ChevronRight className="h-4 w-4" />
          </span>
        )}
      </div>
    </div>
  );
}
