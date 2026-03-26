export interface Company {
  id: string;
  name: string;
  normalized_name: string;
  website: string | null;
  created_at: string;
}

export interface CompanyDetail extends Company {
  funding_rounds: FundingRound[];
}

export interface Investor {
  id: string;
  name: string;
  normalized_name: string;
}

export interface FundingRound {
  id: string;
  company_id: string;
  round_type: string;
  amount_usd: string | null;
  valuation_usd: string | null;
  announced_date: string | null;
  source_url: string | null;
  created_at: string;
  investors: Investor[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
