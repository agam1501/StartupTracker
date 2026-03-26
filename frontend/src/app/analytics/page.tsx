import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FundingBySectorChart } from "@/components/charts/FundingBySectorChart";
import { TopInvestorsChart } from "@/components/charts/TopInvestorsChart";
import { SectorSummaryTable } from "@/components/charts/SectorSummaryTable";
import { RoundTypeChart } from "@/components/charts/RoundTypeChart";
import {
  getFundingBySector,
  getTopInvestors,
  getSectorSummary,
  getRoundTypeDistribution,
  getCoInvestors,
} from "@/lib/api";

export default async function AnalyticsPage() {
  let fundingBySector;
  let topInvestors;
  let sectorSummary;
  let roundTypes;
  let coInvestors;
  let error: string | null = null;

  try {
    [fundingBySector, topInvestors, sectorSummary, roundTypes, coInvestors] =
      await Promise.all([
        getFundingBySector(),
        getTopInvestors({ limit: 10 }),
        getSectorSummary(),
        getRoundTypeDistribution(),
        getCoInvestors({ limit: 10 }),
      ]);
  } catch {
    error = "Failed to load analytics. Is the backend running?";
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="p-4 text-sm text-red-700">{error}</CardContent>
      </Card>
    );
  }

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-sm text-gray-500">
          Market intelligence and funding trends.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Funding by Sector */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Funding by Sector</CardTitle>
          </CardHeader>
          <CardContent>
            <FundingBySectorChart data={fundingBySector || []} />
          </CardContent>
        </Card>

        {/* Round Type Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Round Type Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <RoundTypeChart data={roundTypes || []} />
          </CardContent>
        </Card>

        {/* Top Investors */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Top Investors by Deal Count
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TopInvestorsChart data={topInvestors || []} />
          </CardContent>
        </Card>

        {/* Co-Investor Pairs */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Most Frequent Co-Investor Pairs
            </CardTitle>
          </CardHeader>
          <CardContent>
            {coInvestors && coInvestors.length > 0 ? (
              <div className="space-y-2">
                {coInvestors.map((pair, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2.5"
                  >
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium text-gray-900">
                        {pair.investor_a}
                      </span>
                      <span className="text-gray-400">&</span>
                      <span className="font-medium text-gray-900">
                        {pair.investor_b}
                      </span>
                    </div>
                    <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                      {pair.shared_deals} deals
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-8 text-center text-sm text-gray-400">No data</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Sector Summary Table - full width */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Sector Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <SectorSummaryTable data={sectorSummary || []} />
        </CardContent>
      </Card>
    </>
  );
}
