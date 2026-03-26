import { Suspense } from "react";
import Link from "next/link";
import Badge from "@/components/Badge";
import Pagination from "@/components/Pagination";
import { getFundingRounds } from "@/lib/api";
import { formatUSD, formatDate } from "@/lib/format";

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
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Funding Rounds</h1>
        <p className="mt-2 text-gray-600">
          Browse all tracked funding rounds.
        </p>
      </div>

      <div className="mb-6 flex flex-wrap gap-2">
        <Link
          href="/funding-rounds"
          className={`rounded-full border px-3 py-1 text-sm ${
            !roundType
              ? "border-blue-600 bg-blue-50 text-blue-700"
              : "border-gray-300 text-gray-600 hover:bg-gray-50"
          }`}
        >
          All
        </Link>
        {ROUND_TYPES.map((rt) => (
          <Link
            key={rt}
            href={`/funding-rounds?round_type=${encodeURIComponent(rt)}`}
            className={`rounded-full border px-3 py-1 text-sm ${
              roundType === rt
                ? "border-blue-600 bg-blue-50 text-blue-700"
                : "border-gray-300 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {rt}
          </Link>
        ))}
      </div>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      ) : data ? (
        <>
          <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Company
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Round
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Investors
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.items.map((round) => (
                  <tr key={round.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <Link
                        href={`/companies/${round.company_id}`}
                        className="font-medium text-blue-600 hover:underline"
                      >
                        {round.company_id.slice(0, 8)}...
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <Badge label={round.round_type} />
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {formatUSD(round.amount_usd)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatDate(round.announced_date)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {round.investors.map((i) => i.name).join(", ") || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.items.length === 0 && (
            <p className="py-12 text-center text-gray-500">
              No funding rounds{roundType ? ` of type "${roundType}"` : ""}.
            </p>
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
    </main>
  );
}
