import { Suspense } from "react";
import Link from "next/link";
import { Handshake } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import FilterBar from "@/components/FilterBar";
import Pagination from "@/components/Pagination";
import { getAcquisitions } from "@/lib/api";
import { formatUSD, formatDate } from "@/lib/format";
import type { Acquisition } from "@/lib/types";

interface PageProps {
  searchParams: Promise<{
    sort_by?: string;
    sort_order?: string;
    page?: string;
  }>;
}

export default async function AcquisitionsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const sortBy = params.sort_by || "";
  const sortOrder = params.sort_order || "";
  const page = parseInt(params.page || "1", 10);

  let data;
  let error: string | null = null;
  try {
    data = await getAcquisitions({
      sort_by: sortBy || undefined,
      sort_order: sortOrder || undefined,
      page,
      page_size: 20,
    });
  } catch {
    error = "Failed to load acquisitions. Is the backend running?";
  }

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Acquisitions</h1>
        <p className="text-sm text-gray-500">
          Browse tracked acquisition activity.
        </p>
      </div>

      <div className="mb-6">
        <Suspense fallback={null}>
          <FilterBar
            basePath="/acquisitions"
            sortOptions={[
              { label: "Date", value: "date" },
              { label: "Amount", value: "amount" },
            ]}
          />
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
          <Card>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr className="bg-gray-50/50">
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Acquirer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Target
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Confidence
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.items.map((acq: Acquisition) => (
                    <tr
                      key={acq.id}
                      className="transition-colors hover:bg-gray-50/50"
                    >
                      <td className="whitespace-nowrap px-6 py-4">
                        <Link
                          href={`/companies/${acq.acquirer_id}`}
                          className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {acq.acquirer_name || acq.acquirer_id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <Link
                          href={`/companies/${acq.target_id}`}
                          className="font-medium text-gray-900 hover:text-blue-600 hover:underline"
                        >
                          {acq.target_name || acq.target_id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                        {formatUSD(acq.amount_usd)}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                        {formatDate(acq.announced_date)}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                        {acq.confidence_score != null ? (
                          <div className="flex items-center gap-1.5">
                            <div className="h-1.5 w-12 rounded-full bg-gray-200">
                              <div
                                className="h-1.5 rounded-full bg-green-500"
                                style={{
                                  width: `${Math.round(acq.confidence_score * 100)}%`,
                                }}
                              />
                            </div>
                            <span className="text-xs">
                              {Math.round(acq.confidence_score * 100)}%
                            </span>
                          </div>
                        ) : (
                          "-"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {data.items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Handshake className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-lg font-medium text-gray-900">
                No acquisitions yet
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Acquisition data will appear here after ingestion.
              </p>
            </div>
          )}

          <div className="mt-6">
            <Pagination
              page={page}
              pageSize={20}
              total={data.total}
              basePath="/acquisitions"
              extraParams={{
                ...(sortBy ? { sort_by: sortBy } : {}),
                ...(sortOrder ? { sort_order: sortOrder } : {}),
              }}
            />
          </div>
        </>
      ) : null}
    </>
  );
}
