/**
 * This module contains all TypeScript type definitions used throughout the application.
 * It includes interfaces for user management, campaign data, analytics, and API responses.
 */
import { type ReactNode } from 'react';

/**
 * User Management Types
 */

/**
 * Represents a user in the system with their permissions and details
 */
export interface UserData {
  /** Unique username for the user */
  username: string;
  /** User's email address */
  email: string;
  /** User's role in the system */
  role: string;
  /** Company the user belongs to */
  company: string;
  /** User's password (hashed when stored) */
  password: string;
  /** Whether user has access to chart features */
  chart_access: boolean;
  /** Whether user can generate reports */
  report_generation_access: boolean;
  /** Whether user can manage other users */
  user_management_access: boolean;
}

/**
 * Database Types
 */

/**
 * Represents the structure of the database
 */
export interface DbStructure {
  /** Test database schema and metadata */
  test_database: Record<string, string | unknown[]>;
}

/**
 * Campaign Management Types
 */

/**
 * Available filter options for campaigns
 */
export interface CampaignFilterOptions {
  /** Categorical filter options */
  categorical: {
    /** Available age group options */
    age_groups: string[];
    /** Available campaign IDs */
    campaign_ids: string[];
    /** Available marketing channels */
    channels: string[];
    /** Available target countries */
    countries: string[];
  };
  /** Date range constraints */
  date_range: {
    /** Latest available date (Unix timestamp) */
    max_date: number | null;
    /** Earliest available date (Unix timestamp) */
    min_date: number | null;
  };
  /** Numeric range statistics */
  numeric_ranges: {
    /** Ad spend statistics */
    ad_spend: NumericRange;
    /** Leads statistics */
    leads: NumericRange;
    /** Revenue statistics */
    revenue: NumericRange;
    /** Views statistics */
    views: NumericRange;
  };
}

/**
 * Statistics for numeric ranges
 */
interface NumericRange {
  /** Average value */
  avg: number;
  /** Maximum value */
  max: number;
  /** Minimum value */
  min: number;
}

/**
 * Filter criteria for querying campaigns
 */
export interface CampaignFilters {
  /** Filter by marketing channels */
  channels?: string[];
  /** Filter by target countries */
  countries?: string[];
  /** Filter by age groups */
  age_groups?: string[];
  /** Filter by campaign IDs */
  campaign_ids?: string[];
  /** Start date for date range (Unix timestamp) */
  from_date?: number;
  /** End date for date range (Unix timestamp) */
  to_date?: number;
  /** Minimum revenue threshold */
  min_revenue?: number;
  /** Maximum revenue threshold */
  max_revenue?: number;
  /** Minimum ad spend threshold */
  min_ad_spend?: number;
  /** Maximum ad spend threshold */
  max_ad_spend?: number;
  /** Minimum views threshold */
  min_views?: number;
  /** Minimum leads threshold */
  min_leads?: number;
  /** Field to sort results by */
  sort_by?: string;
  /** Sort direction ('asc' or 'desc') */
  sort_dir?: string;
  /** Page number for pagination */
  page?: number;
  /** Number of items per page */
  page_size?: number;
}

/**
 * Campaign data item returned from filter queries
 */
interface FilteredData {
  /** Campaign date (Unix timestamp) */
  date: number;
  /** Amount spent on advertising */
  ad_spend: string;
  /** Target age group */
  age_group: string;
  /** Unique campaign identifier */
  campaign_id: string;
  /** Marketing channel used */
  channel: string;
  /** Target country */
  country: string;
  /** Number of leads generated */
  leads: string;
  /** Number of new accounts created */
  new_accounts: string;
  /** Revenue generated */
  revenue: string;
  /** Number of views/impressions */
  views: string;
}

/**
 * Response from campaign filter queries
 */
export interface FilterResponse {
  /** Array of filtered campaign data */
  data: FilteredData[];
  /** Total number of matching records */
  total: number;
  /** Current page number */
  page: number;
  /** Number of items per page */
  page_size: number;
  /** Total number of pages */
  total_pages: number;
}

/**
 * Data Import Types
 */

/**
 * Response from CSV file upload endpoint
 */
export interface CsvUploadResponse {
  /** Status message */
  message: string;
  /** Number of records processed */
  count: number;
  /** Target collection name */
  collection: string;
}

/**
 * Analytics Types
 */

/**
 * Monthly performance metrics
 */
interface MonthlyAggregatedItem {
  /** Month (Unix timestamp) */
  date: number;
  /** Total revenue for the month */
  revenue: number;
  /** Total ad spend for the month */
  ad_spend: number;
  /** Total views/impressions */
  views: number;
  /** Total leads generated */
  leads: number;
  /** Total new accounts created */
  new_accounts: number;
}

/**
 * Monthly performance data with applied filters
 */
export interface MonthlyPerformanceData {
  /** Array of monthly metrics */
  items: MonthlyAggregatedItem[];
  /** Filters applied to the data */
  filters: CampaignFilters;
}

/**
 * Last 12 months of performance data
 */
export interface LatestTwelveMonthsData {
  /** Array of monthly metrics */
  items: Array<{
    /** Month (Unix timestamp) */
    date: number;
    /** Total revenue */
    revenue: number;
    /** Total ad spend */
    ad_spend: number;
    /** Total new accounts */
    new_accounts: number;
  }>;
}

/**
 * Channel contribution metrics
 */
interface ChannelMetricValues {
  /** Metric name */
  metric: string;
  /** Values by channel */
  values: Record<string, number>;
}

/**
 * Channel contribution analysis data
 */
export interface ChannelContributionData {
  /** Available metrics */
  metrics: string[];
  /** Available channels */
  channels: string[];
  /** Contribution data */
  data: ChannelMetricValues[];
  /** Analysis time range */
  time_range?: TimeRange;
  /** Error message if any */
  error?: string | null;
}

/**
 * Time range specification
 */
interface TimeRange {
  /** Start date as Unix timestamp */
  from_: number | null;
  /** End date as Unix timestamp */
  to: number | null;
}

/**
 * Cost metrics visualization types
 */
interface HeatmapCell {
  /** Cell value */
  value: number;
  /** Normalized intensity (0-1) */
  intensity: number;
}

/**
 * Row in the cost metrics heatmap
 */
interface HeatmapRow {
  /** Metric name */
  metric: string;
  /** Values by channel */
  values: Record<string, HeatmapCell>;
}

/**
 * Cost metrics heatmap data
 */
export interface CostMetricsHeatmapData {
  /** Available metrics */
  metrics: string[];
  /** Available channels */
  channels: string[];
  /** Heatmap data */
  data: HeatmapRow[];
  /** Analysis time range */
  time_range?: TimeRange;
  /** Error message if any */
  error?: string | null;
}

/**
 * Latest performance metrics
 */

/**
 * Latest month's ROI data
 */
export interface LatestMonthROI {
  /** ROI percentage */
  roi: number;
  /** Month number (1-12) */
  month: number;
  /** Year */
  year: number;
  /** Error message if any */
  error: string | null;
}

/**
 * Latest month's revenue data
 */
export interface LatestMonthRevenue {
  /** Total revenue */
  revenue: number;
  /** Month number (1-12) */
  month: number;
  /** Year */
  year: number;
  /** Error message if any */
  error: string | null;
}

/**
 * Prophet Prediction Types
 */

/**
 * Prophet prediction data point
 */
export interface ProphetPredictionData {
  /** Prediction date (Unix timestamp) */
  date: number;
  /** Predicted revenue */
  revenue: number;
  /** Predicted ad spend */
  ad_spend: number;
  /** Predicted new accounts */
  new_accounts: number;
}

/**
 * Prophet prediction API response
 */
export interface ProphetPredictionResponse {
  /** Prediction results */
  data: {
    /** Number of predictions */
    count: number;
    /** Array of predictions */
    data: ProphetPredictionData[];
  };
  /** HTTP status code */
  status: number;
  /** Whether the request was successful */
  success: boolean;
}

/**
 * Monthly Breakdown Types
 */

/**
 * Base interface for monthly breakdowns
 */
interface MonthlyBreakdownBase {
  /** Array of months (Unix timestamps) */
  months: number[];
  /** Revenue by category */
  revenue: Record<string, number[]>;
  /** Ad spend by category */
  ad_spend: Record<string, number[]>;
}

/**
 * Monthly data broken down by channel
 */
export interface MonthlyChannelData extends MonthlyBreakdownBase {
  /** Available marketing channels */
  channels: string[];
}

/**
 * Monthly data broken down by age group
 */
export interface MonthlyAgeData extends MonthlyBreakdownBase {
  /** Available age groups */
  age_groups: string[];
}

/**
 * Monthly data broken down by country
 */
export interface MonthlyCountryData extends MonthlyBreakdownBase {
  /** Available countries */
  countries: string[];
}

/**
 * Prophet Pipeline Types
 */

/**
 * Prophet pipeline status response
 */
export interface ProphetPipelineResponse {
  /** Current pipeline status */
  status: 'started' | 'in_progress' | 'success' | 'error' | 'idle' | 'skipped' | 'lock_failed';
  /** Status message */
  message: string;
  /** Whether prediction is currently running */
  is_running?: boolean;
  /** Information about the last prediction run */
  last_prediction?: {
    /** Number of months that were forecast */
    forecast_months: number;
    /** Timestamp of when the prediction was run */
    timestamp: number;
    /** Status of the last prediction run */
    status:
      | 'not_run'
      | 'starting'
      | 'running'
      | 'completed'
      | 'failed'
      | 'error'
      | 'skipped'
      | 'lock_failed'
      | 'success';
  };
}

/**
 * LLM API Types
 */

/**
 * Request object for LLM query API
 */
export interface QueryRequest {
  /** The natural language query string */
  query: string;
}

/**
 * Response types for different query classifications
 */
export type QueryResultType = 'chart' | 'description' | 'report' | 'error' | 'unknown';

/**
 * Report results returned from the API
 */
interface ReportResults {
  /** Array of results that can be either text descriptions or base64-encoded chart data */
  results: Array<string>;
}

/**
 * Processed query result for frontend display
 */
export interface ProcessedQueryResult {
  /** The type of result */
  type: QueryResultType;
  /** The processed content ready for display */
  content: string | Array<string | ReactNode> | null;
  /** The original query that was sent */
  originalQuery: string;
}

/**
 * Response from the LLM query API
 */
export interface QueryResponse {
  /** The query output with type and result */
  output: {
    /** Type of result returned */
    type: QueryResultType;
    /** The actual result data, varies based on type */
    result: string | ReportResults;
  };
  /** The original query that was sent */
  original_query: string;
}

/**
 * Response from the LLM API health check
 */
export interface HealthResponse {
  /** Status message */
  status: 'ok' | 'error';
  /** Detailed message about the health status */
  message: string;
  /** Whether the API is healthy */
  healthy: boolean;
  /** Number of available collections (only if healthy) */
  collections_count?: number;
}

/**
 * Database List Response
 */
export interface DatabaseListResponse {
  databases: string[];
}

/**
 * Database Delete Response
 */
export interface DatabaseDeleteResponse {
  message: string;
  database: string;
}
