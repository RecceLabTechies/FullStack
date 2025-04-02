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
    max_date: number;
    min_date: number;
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
  from_date?: number;
  to_date?: number;
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

interface FilteredData {
  date: number;
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

// API response interfaces
export interface CsvUploadResponse {
  message: string;
  count: number;
  collection: string;
}

// Monthly performance data interfaces
interface MonthlyAggregatedItem {
  date: number; // Unix timestamp for the month
  revenue: number;
  ad_spend: number;
  views: number;
  leads: number;
  new_accounts: number;
}

export interface MonthlyPerformanceData {
  items: MonthlyAggregatedItem[];
  filters: CampaignFilters;
}

export interface LatestTwelveMonthsData {
  items: {
    date: number;
    revenue: number;
    ad_spend: number;
    new_accounts: number;
  }[];
}

// Channel contribution data interfaces
interface ChannelMetricValues {
  metric: string;
  values: Record<string, number>;
}

export interface ChannelContributionData {
  metrics: string[];
  channels: string[];
  data: ChannelMetricValues[];
  time_range?: {
    from_: string | null;
    to: string | null;
  };
  error?: string | null;
}

// Cost metrics heatmap interfaces
interface HeatmapCell {
  value: number;
  intensity: number;
}

interface HeatmapRow {
  metric: string;
  values: Record<string, HeatmapCell>;
}

export interface CostMetricsHeatmapData {
  metrics: string[];
  channels: string[];
  data: HeatmapRow[];
  time_range?: {
    from_: string | null;
    to: string | null;
  };
  error?: string | null;
}

/**
 * Response type for latest month ROI endpoint
 */
export interface LatestMonthROI {
  roi: number;
  month: number;
  year: number;
  error: string | null;
}

/**
 * Response type for latest month revenue endpoint
 */
export interface LatestMonthRevenue {
  revenue: number;
  month: number;
  year: number;
  error: string | null;
}

export interface ProphetPredictionData {
  date: number;
  revenue: number;
  ad_spend: number;
  new_accounts: number;
}

export interface ProphetPredictionResponse {
  data: {
    count: number;
    data: ProphetPredictionData[];
  };
  status: number;
  success: boolean;
}

export interface MonthlyChannelData {
  months: number[];
  channels: string[];
  revenue: Record<string, number[]>;
  ad_spend: Record<string, number[]>;
}

export interface MonthlyAgeData {
  months: number[];
  age_groups: string[];
  revenue: Record<string, number[]>;
  ad_spend: Record<string, number[]>;
}

/**
 * Monthly data aggregated by country for charting purposes.
 */
export interface MonthlyCountryData {
  months: number[]; // Array of Unix timestamps
  countries: string[]; // Array of country names
  revenue: Record<string, number[]>; // Map of country to revenue values per month
  ad_spend: Record<string, number[]>; // Map of country to ad spend values per month
}
