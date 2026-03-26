import { Suspense } from "react";
import Link from "next/link";
import SearchBar from "@/components/SearchBar";
import Pagination from "@/components/Pagination";
import Badge from "@/components/Badge";
import { getCompanies } from "@/lib/api";
import { formatUSD } from "@/lib/format";
import type { Company } from "@/lib/types";

interface PageProps {
  searchParams: Promise<{ search?: string; page?: string }>;
}

export default async function Home({ searchParams }: PageProps) {
  const params = await searchParams;
  const search = params.search || "";
  const page = parseInt(params.page || "1", 10);

  let data;
  let error: string | null = null;
  try {
    data = await getCompanies({ search: search || undefined, page, page_size: 20 });
  } catch {
    error = "Failed to load companies. Is the backend running?";
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Companies</h1>
        <p className="mt-2 text-gray-600">
          Browse and search startup funding data.
        </p>
      </div>

      <div className="mb-6">
        <Suspense fallback={null}>
          <SearchBar />
        </Suspense>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      ) : data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((company: Company) => (
              <Link
                key={company.id}
                href={`/companies/${company.id}`}
                className="block rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md"
              >
                <h2 className="text-lg font-semibold text-gray-900">
                  {company.name}
                </h2>
                {company.website && (
                  <p className="mt-1 text-sm text-gray-500 truncate">
                    {company.website}
                  </p>
                )}
              </Link>
            ))}
          </div>

          {data.items.length === 0 && (
            <p className="py-12 text-center text-gray-500">
              {search ? `No companies matching "${search}"` : "No companies yet."}
            </p>
          )}

          <div className="mt-6">
            <Pagination
              page={page}
              pageSize={20}
              total={data.total}
              basePath="/"
              extraParams={search ? { search } : {}}
            />
          </div>
        </>
      ) : null}
    </main>
  );
}
