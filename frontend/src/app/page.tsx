import { Suspense } from "react";
import Link from "next/link";
import { Building2, TrendingUp, Users, DollarSign, Globe } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectorBadge } from "@/components/ui/sector-badge";
import { Skeleton } from "@/components/ui/skeleton";
import SearchBar from "@/components/SearchBar";
import Pagination from "@/components/Pagination";
import { getCompanies, getStats } from "@/lib/api";
import { formatUSD } from "@/lib/format";
import type { Company, Stats } from "@/lib/types";

async function StatsBar() {
  let stats: Stats | null = null;
  try {
    stats = await getStats();
  } catch {
    return null;
  }
  if (!stats) return null;

  const items = [
    {
      label: "Companies",
      value: stats.total_companies.toLocaleString(),
      icon: Building2,
    },
    {
      label: "Funding Rounds",
      value: stats.total_rounds.toLocaleString(),
      icon: TrendingUp,
    },
    {
      label: "Investors",
      value: stats.total_investors.toLocaleString(),
      icon: Users,
    },
    {
      label: "Total Funding",
      value: formatUSD(String(stats.total_funding_usd)),
      icon: DollarSign,
    },
  ];

  return (
    <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {items.map(({ label, value, icon: Icon }) => (
        <Card key={label}>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-lg bg-blue-50 p-2.5">
              <Icon className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">{label}</p>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function StatsBarSkeleton() {
  return (
    <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[...Array(4)].map((_, i) => (
        <Card key={i}>
          <CardContent className="flex items-center gap-4 p-5">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <div className="space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-7 w-16" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function CompanyCard({ company }: { company: Company }) {
  const initials = company.name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <Link
      href={`/companies/${company.id}`}
      className="group block"
    >
      <Card className="h-full transition-all group-hover:shadow-md group-hover:border-blue-200">
        <CardContent className="flex items-start gap-4 p-5">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-sm font-bold text-white">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
              {company.name}
            </h3>
            {company.sector && (
              <div className="mt-1">
                <SectorBadge sector={company.sector} />
              </div>
            )}
            {company.website && (
              <p className="mt-0.5 flex items-center gap-1 text-sm text-gray-400 truncate">
                <Globe className="h-3 w-3" />
                {company.website.replace(/^https?:\/\//, "")}
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

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
    data = await getCompanies({
      search: search || undefined,
      page,
      page_size: 21,
    });
  } catch {
    error = "Failed to load companies. Is the backend running?";
  }

  return (
    <>
      <Suspense fallback={<StatsBarSkeleton />}>
        <StatsBar />
      </Suspense>

      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Companies</h1>
          <p className="text-sm text-gray-500">
            Browse and search startup funding data.
          </p>
        </div>
      </div>

      <div className="mb-6">
        <Suspense fallback={null}>
          <SearchBar />
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
            {data.items.map((company: Company) => (
              <CompanyCard key={company.id} company={company} />
            ))}
          </div>

          {data.items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Building2 className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-lg font-medium text-gray-900">
                {search ? "No results found" : "No companies yet"}
              </p>
              <p className="mt-1 text-sm text-gray-500">
                {search
                  ? `Try a different search term`
                  : "Companies will appear here after ingestion."}
              </p>
            </div>
          )}

          <div className="mt-6">
            <Pagination
              page={page}
              pageSize={21}
              total={data.total}
              basePath="/"
              extraParams={search ? { search } : {}}
            />
          </div>
        </>
      ) : null}
    </>
  );
}
