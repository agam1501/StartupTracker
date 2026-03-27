"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, Search, Users } from "lucide-react";
import { globalSearch } from "@/lib/api";
import type { SearchResult, SearchResults } from "@/lib/types";

export default function GlobalSearch() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null);

  // Flatten results for keyboard nav
  const allItems: { type: "company" | "investor"; item: SearchResult }[] = [];
  if (results) {
    for (const c of results.companies) allItems.push({ type: "company", item: c });
    for (const i of results.investors) allItems.push({ type: "investor", item: i });
  }

  const navigate = useCallback(
    (type: "company" | "investor", id: string) => {
      setOpen(false);
      setQuery("");
      setResults(null);
      if (type === "company") router.push(`/companies/${id}`);
      else router.push(`/investors/${id}`);
    },
    [router],
  );

  // Cmd+K listener
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setQuery("");
      setResults(null);
      setActiveIndex(0);
    }
  }, [open]);

  // Debounced search
  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);

    if (query.length < 2) {
      setResults(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    timerRef.current = setTimeout(async () => {
      try {
        const data = await globalSearch(query);
        setResults(data);
        setActiveIndex(0);
      } catch {
        setResults(null);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [query]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      setOpen(false);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((prev) => Math.min(prev + 1, allItems.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((prev) => Math.max(prev - 1, 0));
    } else if (e.key === "Enter" && allItems[activeIndex]) {
      e.preventDefault();
      const { type, item } = allItems[activeIndex];
      navigate(type, item.id);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center bg-black/50 pt-[15vh]"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-lg overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-gray-200 px-4 py-3">
          <Search className="h-5 w-5 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search companies and investors..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 text-sm text-gray-900 placeholder-gray-400 outline-none"
          />
          <kbd className="rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 text-xs text-gray-400">
            Esc
          </kbd>
        </div>

        {loading && (
          <div className="px-4 py-6 text-center text-sm text-gray-400">
            Searching...
          </div>
        )}

        {!loading && results && allItems.length === 0 && (
          <div className="px-4 py-6 text-center text-sm text-gray-400">
            No results found
          </div>
        )}

        {!loading && results && allItems.length > 0 && (
          <div className="max-h-80 overflow-y-auto py-2">
            {results.companies.length > 0 && (
              <>
                <div className="px-4 py-1.5 text-xs font-medium uppercase tracking-wider text-gray-400">
                  Companies
                </div>
                {results.companies.map((c, i) => (
                  <button
                    key={c.id}
                    className={`flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                      activeIndex === i ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50"
                    }`}
                    onClick={() => navigate("company", c.id)}
                    onMouseEnter={() => setActiveIndex(i)}
                  >
                    <Building2 className="h-4 w-4 shrink-0 text-gray-400" />
                    <span className="font-medium">{c.name}</span>
                    {c.sector && (
                      <span className="ml-auto text-xs text-gray-400">{c.sector}</span>
                    )}
                  </button>
                ))}
              </>
            )}
            {results.investors.length > 0 && (
              <>
                <div className="px-4 py-1.5 text-xs font-medium uppercase tracking-wider text-gray-400">
                  Investors
                </div>
                {results.investors.map((inv, i) => {
                  const idx = results.companies.length + i;
                  return (
                    <button
                      key={inv.id}
                      className={`flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors ${
                        activeIndex === idx ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50"
                      }`}
                      onClick={() => navigate("investor", inv.id)}
                      onMouseEnter={() => setActiveIndex(idx)}
                    >
                      <Users className="h-4 w-4 shrink-0 text-gray-400" />
                      <span className="font-medium">{inv.name}</span>
                      {inv.investor_type && (
                        <span className="ml-auto text-xs text-gray-400">
                          {inv.investor_type}
                        </span>
                      )}
                    </button>
                  );
                })}
              </>
            )}
          </div>
        )}

        {!loading && !results && query.length === 0 && (
          <div className="px-4 py-6 text-center text-sm text-gray-400">
            Type to search companies and investors
          </div>
        )}
      </div>
    </div>
  );
}
