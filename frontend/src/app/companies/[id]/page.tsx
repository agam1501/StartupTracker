import { notFound } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Globe,
  DollarSign,
  Calendar,
  ExternalLink,
  Users,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RoundBadge } from "@/components/ui/badge";
import { SectorBadge } from "@/components/ui/sector-badge";
import { getCompany } from "@/lib/api";
import { formatUSD, formatDate } from "@/lib/format";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function CompanyDetailPage({ params }: PageProps) {
  const { id } = await params;

  let company;
  try {
    company = await getCompany(id);
  } catch {
    notFound();
  }

  const totalRaised = company.funding_rounds.reduce((sum, r) => {
    return sum + (r.amount_usd ? parseFloat(r.amount_usd) : 0);
  }, 0);

  const allInvestors = new Map<string, string>();
  for (const round of company.funding_rounds) {
    for (const inv of round.investors) {
      allInvestors.set(inv.id, inv.name);
    }
  }

  const initials = company.name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <>
      <Link
        href="/"
        className="mb-6 inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to companies
      </Link>

      {/* Header */}
      <Card className="mb-8">
        <CardContent className="flex flex-col gap-6 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-lg font-bold text-white">
              {initials}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {company.name}
              </h1>
              {company.sector && (
                <div className="mt-1">
                  <SectorBadge sector={company.sector} />
                </div>
              )}
              {company.website && (
                <a
                  href={company.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-0.5 flex items-center gap-1 text-sm text-blue-600 hover:underline"
                >
                  <Globe className="h-3.5 w-3.5" />
                  {company.website.replace(/^https?:\/\//, "")}
                </a>
              )}
            </div>
          </div>
          <div className="flex gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {company.funding_rounds.length}
              </p>
              <p className="text-xs text-gray-500">Rounds</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {totalRaised > 0 ? formatUSD(String(totalRaised)) : "-"}
              </p>
              <p className="text-xs text-gray-500">Total Raised</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900">
                {allInvestors.size}
              </p>
              <p className="text-xs text-gray-500">Investors</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Funding Timeline */}
        <div className="lg:col-span-2">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Funding Timeline
          </h2>
          {company.funding_rounds.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center py-12 text-center">
                <DollarSign className="mb-3 h-10 w-10 text-gray-300" />
                <p className="text-gray-500">No funding rounds recorded.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="relative space-y-0">
              {/* Timeline line */}
              <div className="absolute left-[19px] top-2 bottom-2 w-px bg-gray-200" />

              {company.funding_rounds.map((round, idx) => (
                <div key={round.id} className="relative flex gap-4 pb-6">
                  {/* Timeline dot */}
                  <div className="relative z-10 mt-1.5 flex h-[10px] w-[10px] shrink-0 items-center justify-center rounded-full border-2 border-blue-500 bg-white ring-4 ring-white" />

                  <Card className="flex-1">
                    <CardContent className="p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <RoundBadge roundType={round.round_type} />
                          <span className="text-lg font-semibold text-gray-900">
                            {formatUSD(round.amount_usd)}
                          </span>
                        </div>
                        <span className="flex items-center gap-1 text-sm text-gray-400">
                          <Calendar className="h-3.5 w-3.5" />
                          {formatDate(round.announced_date)}
                        </span>
                      </div>

                      {round.valuation_usd && (
                        <p className="mt-2 text-sm text-gray-500">
                          Valuation: {formatUSD(round.valuation_usd)}
                        </p>
                      )}

                      {round.investors.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {round.investors.map((inv) => (
                            <span
                              key={inv.id}
                              className="rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600"
                            >
                              {inv.name}
                            </span>
                          ))}
                        </div>
                      )}

                      {round.confidence_score != null && (
                        <div className="mt-2 flex items-center gap-1.5">
                          <div className="h-1.5 w-16 rounded-full bg-gray-200">
                            <div
                              className="h-1.5 rounded-full bg-green-500"
                              style={{ width: `${Math.round(round.confidence_score * 100)}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-400">
                            {Math.round(round.confidence_score * 100)}% confidence
                          </span>
                        </div>
                      )}

                      {round.source_url && (
                        <a
                          href={round.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-2 inline-flex items-center gap-1 text-xs text-blue-500 hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" />
                          Source
                        </a>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar: Investors */}
        <div>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Investors
          </h2>
          {allInvestors.size === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center py-8 text-center">
                <Users className="mb-2 h-8 w-8 text-gray-300" />
                <p className="text-sm text-gray-500">No investors recorded.</p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-4">
                <div className="space-y-2">
                  {[...allInvestors.entries()].map(([invId, name]) => {
                    const investorInitials = name
                      .split(" ")
                      .slice(0, 2)
                      .map((w) => w[0])
                      .join("")
                      .toUpperCase();
                    return (
                      <div
                        key={invId}
                        className="flex items-center gap-3 rounded-lg p-2 hover:bg-gray-50"
                      >
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-medium text-gray-600">
                          {investorInitials}
                        </div>
                        <span className="text-sm font-medium text-gray-700">
                          {name}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
