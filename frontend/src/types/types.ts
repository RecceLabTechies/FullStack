export interface CampaignData {
  date: string; // Format: YYYY-MM-DD, stored as datetime in backend
  campaign_id: string;
  channel: string;
  age_group: string;
  ad_spend: number;
  views: number;
  leads: number;
  new_accounts: number;
  country: string;
  revenue: number;
}

export interface UserData {
  username: string;
  email: string;
  role: string;
  company: string;
  password: string;
  chart_access: boolean;
  report_generation_access: boolean;
  user_management_access: boolean;
}

// Database structure interfaces
export interface DbStructure {
  test_database: Record<string, string | unknown[]>;
}

// Campaign filter interfaces
export interface CampaignFilterOptions {
  categorical: {
    age_groups: string[];
    campaign_ids: string[];
    channels: string[];
    countries: string[];
  };
  date_range: {
    max_date: string;
    min_date: string;
  };
  numeric_ranges: {
    ad_spend: { avg: number; max: number; min: number };
    leads: { avg: number; max: number; min: number };
    revenue: { avg: number; max: number; min: number };
    views: { avg: number; max: number; min: number };
  };
}

export interface CampaignFilters {
  channels?: string[];
  countries?: string[];
  age_groups?: string[];
  campaign_ids?: string[];
  from_date?: string;
  to_date?: string;
  min_revenue?: number;
  max_revenue?: number;
  min_ad_spend?: number;
  max_ad_spend?: number;
  min_views?: number;
  min_leads?: number;
  sort_by?: string;
  sort_dir?: string;
  page?: number;
  page_size?: number;
}

export interface FilteredData {
  Date: string;
  ad_spend: string;
  age_group: string;
  campaign_id: string;
  channel: string;
  country: string;
  leads: string;
  new_accounts: string;
  revenue: string;
  views: string;
}

export interface FilterResponse {
  data: FilteredData[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Analytics data interfaces
export interface RevenueData {
  date: string;
  revenue: number;
}

export interface ChannelRoi {
  channel: string;
  roi: number;
}

export interface AgeGroupRoi {
  age_group: string;
  roi: number;
}

export interface RevenuePastMonth {
  revenue: number;
}

export interface RoiPastMonth {
  roi: number;
}

// Monthly performance data interfaces
export interface MonthlyPerformanceData {
  months: string[];
  revenue: number[];
  ad_spend: number[];
  roi: number[];
}

export interface MonthlyUpdateItem {
  month: string;
  revenue?: number;
  ad_spend?: number;
}

// This is an array of update items to be sent to the API
export type MonthlyUpdateData = MonthlyUpdateItem;

// API response interfaces
export interface CsvUploadResponse {
  message: string;
  count: number;
  collection: string;
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}
