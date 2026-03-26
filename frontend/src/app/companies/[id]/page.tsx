import { notFound } from "next/navigation";
import Link from "next/link";
import Badge from "@/components/Badge";
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

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Link
        href="/"
        className="mb-6 inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
      >
        &larr; Back to companies
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{company.name}</h1>
        {company.website && (
          <a
            href={company.website}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 text-sm text-blue-600 hover:underline"
          >
            {company.website}
          </a>
        )}
      </div>

      <h2 className="mb-4 text-xl font-semibold text-gray-900">
        Funding Rounds ({company.funding_rounds.length})
      </h2>

      {company.funding_rounds.length === 0 ? (
        <p className="text-gray-500">No funding rounds recorded.</p>
      ) : (
        <div className="space-y-4">
          {company.funding_rounds.map((round) => (
            <div
              key={round.id}
              className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Badge label={round.round_type} />
                  <span className="text-lg font-semibold text-gray-900">
                    {formatUSD(round.amount_usd)}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {formatDate(round.announced_date)}
                </span>
              </div>

              {round.valuation_usd && (
                <p className="mt-2 text-sm text-gray-600">
                  Valuation: {formatUSD(round.valuation_usd)}
                </p>
              )}

              {round.investors.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium uppercase text-gray-400">
                    Investors
                  </p>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {round.investors.map((inv) => (
                      <span
                        key={inv.id}
                        className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
                      >
                        {inv.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {round.source_url && (
                <a
                  href={round.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-block text-xs text-blue-500 hover:underline"
                >
                  Source
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
