import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SectorBadge } from "@/components/ui/sector-badge";
import { formatUSD } from "@/lib/format";
import type { FundingRound } from "@/lib/types";

interface InvestorSectorBreakdownProps {
  fundingRounds: FundingRound[];
}

interface SectorData {
  sector: string;
  dealCount: number;
  totalAmount: number;
  companies: Set<string>;
}

export default function InvestorSectorBreakdown({
  fundingRounds,
}: InvestorSectorBreakdownProps) {
  const sectorMap = new Map<string, SectorData>();

  for (const round of fundingRounds) {
    const sector = round.company_sector || "Unknown";
    const existing = sectorMap.get(sector) || {
      sector,
      dealCount: 0,
      totalAmount: 0,
      companies: new Set<string>(),
    };
    existing.dealCount++;
    existing.totalAmount += round.amount_usd ? parseFloat(round.amount_usd) : 0;
    if (round.company_name) existing.companies.add(round.company_name);
    sectorMap.set(sector, existing);
  }

  const sectors = [...sectorMap.values()].sort(
    (a, b) => b.totalAmount - a.totalAmount,
  );

  if (sectors.length === 0) return null;

  const maxAmount = Math.max(...sectors.map((s) => s.totalAmount), 1);

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle>Sector Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {sectors.map((s) => (
          <div key={s.sector}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                {s.sector === "Unknown" ? (
                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                    Unknown
                  </span>
                ) : (
                  <SectorBadge sector={s.sector} />
                )}
                <span className="text-xs text-gray-500">
                  {s.dealCount} {s.dealCount === 1 ? "deal" : "deals"}
                  {" · "}
                  {s.companies.size} {s.companies.size === 1 ? "company" : "companies"}
                </span>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {formatUSD(String(s.totalAmount))}
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-100">
              <div
                className="h-2 rounded-full bg-emerald-500"
                style={{
                  width: `${Math.max((s.totalAmount / maxAmount) * 100, 2)}%`,
                }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
