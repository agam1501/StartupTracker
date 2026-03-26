import type {
  Company,
  CompanyDetail,
  FundingRound,
  Investor,
  PaginatedResponse,
  Stats,
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

export async function getCompanies(params?: {
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Company>> {
  return fetchApi(`/companies${buildQuery(params || {})}`);
}

export async function getCompany(id: string): Promise<CompanyDetail> {
  return fetchApi(`/companies/${id}`);
}

export async function getFundingRounds(params?: {
  company_id?: string;
  round_type?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<FundingRound>> {
  return fetchApi(`/funding-rounds${buildQuery(params || {})}`);
}

export async function getInvestors(params?: {
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Investor>> {
  return fetchApi(`/investors${buildQuery(params || {})}`);
}

export async function getStats(): Promise<Stats> {
  return fetchApi("/stats");
}
