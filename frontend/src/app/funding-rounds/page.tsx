import Link from "next/link";
import { TrendingUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { RoundBadge } from "@/components/ui/badge";
import Pagination from "@/components/Pagination";
import { getFundingRounds } from "@/lib/api";
import { formatUSD, formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

const ROUND_TYPES = [
  "Pre-Seed",
  "Seed",
  "Series A",
  "Series B",
  "Series C",
  "Series D",
];

interface PageProps {
  searchParams: Promise<{ round_type?: string; page?: string }>;
}

export default async function FundingRoundsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const roundType = params.round_type || "";
  const page = parseInt(params.page || "1", 10);

  let data;
  let error: string | null = null;
  try {
    data = await getFundingRounds({
      round_type: roundType || undefined,
      page,
      page_size: 20,
    });
  } catch {
    error = "Failed to load funding rounds. Is the backend running?";
  }

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Funding Rounds</h1>
        <p className="text-sm text-gray-500">
          Browse all tracked funding rounds.
        </p>
      </div>

      {/* Filter pills */}
      <div className="mb-6 flex flex-wrap gap-2">
        <Link
          href="/funding-rounds"
          className={cn(
            "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
            !roundType
              ? "border-blue-600 bg-blue-50 text-blue-700"
              : "border-gray-200 text-gray-600 hover:bg-gray-50"
          )}
        >
          All
        </Link>
        {ROUND_TYPES.map((rt) => (
          <Link
            key={rt}
            href={`/funding-rounds?round_type=${encodeURIComponent(rt)}`}
            className={cn(
              "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
              roundType === rt
                ? "border-blue-600 bg-blue-50 text-blue-700"
                : "border-gray-200 text-gray-600 hover:bg-gray-50"
            )}
          >
            {rt}
          </Link>
        ))}
      </div>

      {error ? (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 text-sm text-red-700">
            {error}
          </CardContent>
        </Card>
      ) : data ? (
        <>
          <Card>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr className="bg-gray-50/50">
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Company
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Round
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Investors
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.items.map((round) => (
                    <tr
                      key={round.id}
                      className="transition-colors hover:bg-gray-50/50"
                    >
                      <td className="whitespace-nowrap px-6 py-4">
                        <Link
                          href={`/companies/${round.company_id}`}
                          className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {round.company_name || round.company_id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <RoundBadge roundType={round.round_type} />
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                        {formatUSD(round.amount_usd)}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                        {formatDate(round.announced_date)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        <div className="flex flex-wrap gap-1">
                          {round.investors.length > 0
                            ? round.investors.map((i) => (
                                <span
                                  key={i.id}
                                  className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600"
                                >
                                  {i.name}
                                </span>
                              ))
                            : "-"}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {data.items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <TrendingUp className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-lg font-medium text-gray-900">
                No funding rounds
              </p>
              <p className="mt-1 text-sm text-gray-500">
                {roundType
                  ? `No ${roundType} rounds found. Try another filter.`
                  : "Funding rounds will appear here after ingestion."}
              </p>
            </div>
          )}

          <div className="mt-6">
            <Pagination
              page={page}
              pageSize={20}
              total={data.total}
              basePath="/funding-rounds"
              extraParams={roundType ? { round_type: roundType } : {}}
            />
          </div>
        </>
      ) : null}
    </>
  );
}
