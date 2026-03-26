import type {
  Company,
  CompanyDetail,
  FundingRound,
  PaginatedResponse,
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

export async function getCompanies(params?: {
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<Company>> {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));
  const qs = query.toString();
  return fetchApi(`/companies${qs ? `?${qs}` : ""}`);
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
  const query = new URLSearchParams();
  if (params?.company_id) query.set("company_id", params.company_id);
  if (params?.round_type) query.set("round_type", params.round_type);
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));
  const qs = query.toString();
  return fetchApi(`/funding-rounds${qs ? `?${qs}` : ""}`);
}
