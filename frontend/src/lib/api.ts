import type {
  Acquisition,
  AcquisitionSummary,
  CoInvestorPair,
  Company,
  CompanyDetail,
  FundingByMonth,
  FundingBySector,
  FundingRound,
  Investor,
  InvestorDetail,
  MonitoredSource,
  PaginatedResponse,
  RoundTypeDistribution,
  SectorSummary,
  Stats,
  TopInvestor,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

function buildQuery(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") query.set(k, String(v));
  }
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

// Companies
export async function getCompanies(params?: {
  search?: string;
  sector?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Company>> {
  return fetchApi(`/companies${buildQuery(params || {})}`);
}

export async function getCompany(id: string): Promise<CompanyDetail> {
  return fetchApi(`/companies/${id}`);
}

// Funding Rounds
export async function getFundingRounds(params?: {
  company_id?: string;
  round_type?: string;
  investor_id?: string;
  min_amount?: number;
  max_amount?: number;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<FundingRound>> {
  return fetchApi(`/funding-rounds${buildQuery(params || {})}`);
}

// Investors
export async function getInvestors(params?: {
  search?: string;
  investor_type?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Investor>> {
  return fetchApi(`/investors${buildQuery(params || {})}`);
}

export async function getInvestor(id: string): Promise<InvestorDetail> {
  return fetchApi(`/investors/${id}`);
}

// Acquisitions
export async function getAcquisitions(params?: {
  acquirer_id?: string;
  target_id?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Acquisition>> {
  return fetchApi(`/acquisitions${buildQuery(params || {})}`);
}

// Stats
export async function getStats(): Promise<Stats> {
  return fetchApi("/stats");
}

// Analytics
export async function getFundingBySector(): Promise<FundingBySector[]> {
  return fetchApi("/analytics/funding-by-sector");
}

export async function getFundingByMonth(params?: {
  sector?: string;
  months?: number;
}): Promise<FundingByMonth[]> {
  return fetchApi(`/analytics/funding-by-month${buildQuery(params || {})}`);
}

export async function getTopInvestors(params?: {
  limit?: number;
}): Promise<TopInvestor[]> {
  return fetchApi(`/analytics/top-investors${buildQuery(params || {})}`);
}

export async function getCoInvestors(params?: {
  limit?: number;
}): Promise<CoInvestorPair[]> {
  return fetchApi(`/analytics/co-investors${buildQuery(params || {})}`);
}

export async function getSectorSummary(): Promise<SectorSummary[]> {
  return fetchApi("/analytics/sector-summary");
}

export async function getAcquisitionsSummary(): Promise<AcquisitionSummary[]> {
  return fetchApi("/analytics/acquisitions-summary");
}

export async function getRoundTypeDistribution(): Promise<RoundTypeDistribution[]> {
  return fetchApi("/analytics/round-type-distribution");
}

// Sources
export async function getSources(params?: {
  source_type?: string;
  active?: boolean;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<MonitoredSource>> {
  const queryParams: Record<string, string | number | undefined> = {
    source_type: params?.source_type,
    page: params?.page,
    page_size: params?.page_size,
  };
  if (params?.active !== undefined) queryParams.active = params.active ? "true" : "false";
  return fetchApi(`/sources${buildQuery(queryParams)}`);
}

export async function createSource(data: {
  name: string;
  url: string;
  source_type: string;
}): Promise<MonitoredSource> {
  return fetchApi("/sources", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSource(
  id: string,
  data: { active?: boolean; name?: string; url?: string; source_type?: string },
): Promise<MonitoredSource> {
  return fetchApi(`/sources/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
