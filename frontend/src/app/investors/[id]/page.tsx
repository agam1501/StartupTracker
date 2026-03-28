import { notFound } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Globe,
  DollarSign,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { RoundBadge } from "@/components/ui/badge";
import { getInvestor } from "@/lib/api";
import { formatUSD, formatDate } from "@/lib/format";
import InvestorSectorBreakdown from "@/components/InvestorSectorBreakdown";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function InvestorDetailPage({ params }: PageProps) {
  const { id } = await params;

  let investor;
  try {
    investor = await getInvestor(id);
  } catch {
    notFound();
  }

  const totalInvested = investor.funding_rounds.reduce((sum, r) => {
    return sum + (r.amount_usd ? parseFloat(r.amount_usd) : 0);
  }, 0);

  const uniqueCompanies = new Set(
    investor.funding_rounds.map((r) => r.company_name).filter(Boolean)
  );

  const initials = investor.name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <>
      <Link
        href="/investors"
        className="mb-6 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to investors
      </Link>

      {/* Header */}
      <Card className="mb-8">
        <CardContent className="flex flex-col gap-6 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-lg font-bold text-white">
              {initials}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {investor.name}
              </h1>
              {investor.investor_type && (
                <span className="mt-0.5 inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                  {investor.investor_type}
                </span>
              )}
              {investor.website && (
                <a
                  href={investor.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-0.5 flex items-center gap-1 text-sm text-blue-600 hover:underline"
                >
                  <Globe className="h-3.5 w-3.5" />
                  {investor.website.replace(/^https?:\/\//, "")}
                </a>
              )}
            </div>
          </div>
          <div className="flex gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {investor.funding_rounds.length}
              </p>
              <p className="text-xs text-gray-500">Deals</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {uniqueCompanies.size}
              </p>
              <p className="text-xs text-gray-500">Companies</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {totalInvested > 0 ? formatUSD(String(totalInvested)) : "-"}
              </p>
              <p className="text-xs text-gray-500">Total Invested</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sector Breakdown */}
      <InvestorSectorBreakdown fundingRounds={investor.funding_rounds} />

      {/* Funding Rounds */}
      <h2 className="mb-4 text-lg font-semibold text-gray-900">
        Investment History
      </h2>

      {investor.funding_rounds.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12 text-center">
            <TrendingUp className="mb-3 h-10 w-10 text-gray-300" />
            <p className="text-gray-500">No funding rounds recorded.</p>
          </CardContent>
        </Card>
      ) : (
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
                    Co-Investors
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {investor.funding_rounds.map((round) => (
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
                        {round.investors
                          .filter((i) => i.id !== investor.id)
                          .map((i) => (
                            <span
                              key={i.id}
                              className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600"
                            >
                              {i.name}
                            </span>
                          ))}
                        {round.investors.filter((i) => i.id !== investor.id)
                          .length === 0 && (
                          <span className="text-gray-400">Solo</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  );
}
