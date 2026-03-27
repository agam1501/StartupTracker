export interface Company {
  id: string;
  name: string;
  normalized_name: string;
  website: string | null;
  sector: string | null;
  revenue_usd: string | null;
  revenue_as_of_date: string | null;
  created_at: string;
}

export interface CompanyDetail extends Company {
  funding_rounds: FundingRound[];
}

export interface Investor {
  id: string;
  name: string;
  normalized_name: string;
  investor_type: string | null;
  website: string | null;
}

export interface InvestorDetail extends Investor {
  funding_rounds: FundingRound[];
}

export interface FundingRound {
  id: string;
  company_id: string;
  company_name: string | null;
  round_type: string;
  amount_usd: string | null;
  valuation_usd: string | null;
  announced_date: string | null;
  source_url: string | null;
  confidence_score: number | null;
  created_at: string;
  investors: Investor[];
}

export interface Acquisition {
  id: string;
  acquirer_id: string;
  acquirer_name: string | null;
  target_id: string;
  target_name: string | null;
  amount_usd: string | null;
  announced_date: string | null;
  source_url: string | null;
  confidence_score: number | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Stats {
  total_companies: number;
  total_rounds: number;
  total_investors: number;
  total_funding_usd: number;
  total_acquisitions: number;
  top_sector: string | null;
}

// Analytics types
export interface FundingBySector {
  sector: string;
  round_count: number;
  total_amount: number;
}

export interface FundingByMonth {
  month: string;
  round_count: number;
  total_amount: number;
}

export interface TopInvestor {
  id: string;
  name: string;
  deal_count: number;
  total_invested: number;
}

export interface CoInvestorPair {
  investor_a: string;
  investor_b: string;
  shared_deals: number;
}

export interface SectorSummary {
  sector: string;
  company_count: number;
  round_count: number;
  total_funding: number;
  avg_round_size: number;
}

export interface AcquisitionSummary {
  id: string;
  name: string;
  acquisition_count: number;
  total_spent: number;
}

export interface RoundTypeDistribution {
  round_type: string;
  count: number;
  total_amount: number;
}
