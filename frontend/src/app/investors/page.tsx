import { Suspense } from "react";
import { Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import SearchBar from "@/components/SearchBar";
import Pagination from "@/components/Pagination";
import { getInvestors } from "@/lib/api";
import type { Investor } from "@/lib/types";

interface PageProps {
  searchParams: Promise<{ search?: string; page?: string }>;
}

function InvestorCard({ investor }: { investor: Investor }) {
  const initials = investor.name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <Card className="transition-all hover:shadow-md hover:border-blue-200">
      <CardContent className="flex items-center gap-4 p-5">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 text-sm font-bold text-white">
          {initials}
        </div>
        <div className="min-w-0">
          <h3 className="font-semibold text-gray-900">{investor.name}</h3>
        </div>
      </CardContent>
    </Card>
  );
}

export default async function InvestorsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const search = params.search || "";
  const page = parseInt(params.page || "1", 10);

  let data;
  let error: string | null = null;
  try {
    data = await getInvestors({
      search: search || undefined,
      page,
      page_size: 24,
    });
  } catch {
    error = "Failed to load investors. Is the backend running?";
  }

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Investors</h1>
        <p className="text-sm text-gray-500">
          Browse all tracked investors.
        </p>
      </div>

      <div className="mb-6">
        <Suspense fallback={null}>
          <SearchBar basePath="/investors" />
        </Suspense>
      </div>

      {error ? (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 text-sm text-red-700">
            {error}
          </CardContent>
        </Card>
      ) : data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((investor: Investor) => (
              <InvestorCard key={investor.id} investor={investor} />
            ))}
          </div>

          {data.items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Users className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-lg font-medium text-gray-900">
                {search ? "No results found" : "No investors yet"}
              </p>
              <p className="mt-1 text-sm text-gray-500">
                {search
                  ? "Try a different search term."
                  : "Investors will appear here after ingestion."}
              </p>
            </div>
          )}

          <div className="mt-6">
            <Pagination
              page={page}
              pageSize={24}
              total={data.total}
              basePath="/investors"
              extraParams={search ? { search } : {}}
            />
          </div>
        </>
      ) : null}
    </>
  );
}
