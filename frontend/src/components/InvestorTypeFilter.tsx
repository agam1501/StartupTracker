"use client";

import { useRouter, useSearchParams } from "next/navigation";

const INVESTOR_TYPES = ["VC", "Angel", "Corporate", "PE", "Accelerator", "Other"];

export default function InvestorTypeFilter() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const current = searchParams.get("investor_type") || "";

  function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const params = new URLSearchParams(searchParams.toString());
    if (e.target.value) {
      params.set("investor_type", e.target.value);
    } else {
      params.delete("investor_type");
    }
    params.delete("page");
    router.push(`/investors?${params.toString()}`);
  }

  return (
    <select
      value={current}
      onChange={handleChange}
      className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
    >
      <option value="">All Types</option>
      {INVESTOR_TYPES.map((type) => (
        <option key={type} value={type}>
          {type}
        </option>
      ))}
    </select>
  );
}
