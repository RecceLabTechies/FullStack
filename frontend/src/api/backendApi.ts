/**
 * This module contains all API calls to the backend server.
 * It provides functions for interacting with users, campaigns, analytics, and database operations.
 * All functions use a consistent error handling pattern, returning either the expected data or an Error object.
 */
import {
  type CampaignFilterOptions,
  type CampaignFilters,
  type ChannelContributionData,
  type CostMetricsHeatmapData,
  type CsvUploadResponse,
  type DatabaseDeleteResponse,
  type DatabaseListResponse,
  type DbStructure,
  type FilterResponse,
  type LatestMonthRevenue,
  type LatestMonthROI,
  type LatestTwelveMonthsData,
  type MonthlyAgeData,
  type MonthlyChannelData,
  type MonthlyCountryData,
  type MonthlyPerformanceData,
  type ProphetPipelineResponse,
  type ProphetPredictionData,
  type ProphetPredictionResponse,
  type UserData,
} from '@/types/types';
import axios from 'axios';

/** Base URL for all API endpoints */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '/api';

/**
 * Standard API response interface used across endpoints
 */
interface ApiResponse<T> {
  data: T;
  status: number;
  success: boolean;
}

/**
 * User response interfaces
 */
interface UserResponse {
  message: string;
  id?: string;
}

/**
 * Database Structure API
 */

/**
 * Fetches the current database structure
 * @returns Database structure containing tables and relationships
 */
export const fetchDbStructure = async (): Promise<DbStructure | Error> => {
  try {
    const response = await axios.get<ApiResponse<DbStructure>>(
      `${API_BASE_URL}/api/v1/database/structure`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch database structure', error);
    return new Error('Failed to fetch database structure');
  }
};

/**
 * User Management API
 */

/**
 * Fetches all users or a specific user if username is provided
 * @param username Optional - Username to fetch a specific user
 * @returns All users or a specific user
 */
export const fetchUsers = async (username?: string): Promise<UserData[] | UserData | Error> => {
  try {
    const url = username
      ? `${API_BASE_URL}/api/v1/users?username=${username}`
      : `${API_BASE_URL}/api/v1/users`;
    const response = await axios.get<UserData[] | UserData>(url);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch users', error);
    return new Error('Failed to fetch users');
  }
};

/**
 * Creates a new user
 * @param user User data with all required fields
 * @returns Success message
 */
export const addUser = async (user: UserData): Promise<string | Error> => {
  try {
    const response = await axios.post<UserResponse>(`${API_BASE_URL}/api/v1/users`, user);
    return response.data.message;
  } catch (error) {
    console.error('Failed to add user', error);
    return new Error('Failed to add user');
  }
};

/**
 * Fetches a user by username
 * @param username Username to search for
 * @returns User data
 */
export const fetchUserByUsername = async (username: string): Promise<UserData | Error> => {
  try {
    const response = await axios.get<UserData>(`${API_BASE_URL}/api/v1/users/${username}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch user by username', error);
    return new Error('Failed to fetch user by username');
  }
};

/**
 * Updates all fields of a user
 * @param username Username of the user to update
 * @param userData Complete user data with new values
 * @returns Success message
 */
export const updateUser = async (username: string, userData: UserData): Promise<string | Error> => {
  try {
    const response = await axios.put<UserResponse>(
      `${API_BASE_URL}/api/v1/users/${username}`,
      userData
    );
    return response.data.message;
  } catch (error) {
    console.error('Failed to update user', error);
    return new Error('Failed to update user');
  }
};

/**
 * Deletes a user
 * @param username Username of the user to delete
 * @returns Success message
 */
export const deleteUser = async (username: string): Promise<string | Error> => {
  try {
    const response = await axios.delete<UserResponse>(`${API_BASE_URL}/api/v1/users/${username}`);
    return response.data.message;
  } catch (error) {
    console.error('Failed to delete user', error);
    return new Error('Failed to delete user');
  }
};

/**
 * Partially updates a user
 * @param username Username of the user to update
 * @param patchData Fields to update
 * @returns Success message
 */
export const patchUser = async (
  username: string,
  patchData: Partial<UserData>
): Promise<string | Error> => {
  try {
    const response = await axios.patch<UserResponse>(
      `${API_BASE_URL}/api/v1/users/${username}`,
      patchData
    );
    return response.data.message;
  } catch (error) {
    console.error('Failed to patch user', error);
    return new Error('Failed to patch user');
  }
};

/**
 * Campaign Management API
 */

/**
 * Fetches available campaign filter options
 * @returns Available filter options for campaigns
 */
export const fetchCampaignFilterOptions = async (): Promise<CampaignFilterOptions | Error> => {
  try {
    const response = await axios.get<ApiResponse<CampaignFilterOptions>>(
      `${API_BASE_URL}/api/v1/campaigns/filter-options`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch campaign filter options', error);
    return new Error('Failed to fetch campaign filter options');
  }
};

/**
 * Fetches filtered campaign data
 * @param filters Filter parameters for campaigns
 * @returns Filtered campaign data
 */
export const fetchCampaigns = async (filters: CampaignFilters): Promise<FilterResponse | Error> => {
  try {
    const response = await axios.post<FilterResponse>(`${API_BASE_URL}/api/v1/campaigns`, filters);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch campaign data', error);
    return new Error('Failed to fetch campaign data');
  }
};

/**
 * Fetches aggregated monthly performance data
 * @param filters Filter criteria for aggregation
 * @returns Monthly performance metrics
 */
export const fetchMonthlyAggregatedData = async (
  filters: CampaignFilters
): Promise<MonthlyPerformanceData | Error> => {
  try {
    const response = await axios.post<ApiResponse<MonthlyPerformanceData>>(
      `${API_BASE_URL}/api/v1/campaigns/monthly-aggregated`,
      filters
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch monthly aggregated data', error);
    return new Error('Failed to fetch monthly aggregated data');
  }
};

/**
 * Data Import API
 */

/**
 * Uploads and processes a CSV file
 * @param file CSV file to upload
 * @returns Processing results
 */
export const uploadCsv = async (file: File): Promise<CsvUploadResponse | Error> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<CsvUploadResponse>(
      `${API_BASE_URL}/api/v1/imports/csv`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Failed to upload CSV', error);
    return new Error('Failed to upload CSV');
  }
};

/**
 * Analytics API
 */

/**
 * Fetches channel contribution data
 * @param minDate Optional - Start date as Unix timestamp
 * @param maxDate Optional - End date as Unix timestamp
 * @returns Channel contribution metrics
 */
export const fetchChannelContribution = async (
  minDate?: number,
  maxDate?: number
): Promise<ChannelContributionData | Error> => {
  try {
    const params = new URLSearchParams();
    if (minDate) params.append('min_date', minDate.toString());
    if (maxDate) params.append('max_date', maxDate.toString());

    const response = await axios.get<ApiResponse<ChannelContributionData>>(
      `${API_BASE_URL}/api/v1/campaigns/channel-contribution${params.toString() ? '?' + params.toString() : ''}`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch channel contribution data', error);
    return new Error('Failed to fetch channel contribution data');
  }
};

/**
 * Fetches cost metrics heatmap data
 * @param minDate Optional - Start date as Unix timestamp
 * @param maxDate Optional - End date as Unix timestamp
 * @returns Cost metrics by channel
 */
export const fetchCostMetricsHeatmap = async (
  minDate?: number,
  maxDate?: number
): Promise<CostMetricsHeatmapData | Error> => {
  try {
    const params = new URLSearchParams();
    if (minDate) params.append('min_date', minDate.toString());
    if (maxDate) params.append('max_date', maxDate.toString());

    const response = await axios.get<ApiResponse<CostMetricsHeatmapData>>(
      `${API_BASE_URL}/api/v1/campaigns/cost-metrics-heatmap${params.toString() ? '?' + params.toString() : ''}`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch cost metrics heatmap data', error);
    return new Error('Failed to fetch cost metrics heatmap data');
  }
};

/**
 * Fetches ROI for the latest month
 * @returns Latest month's ROI data
 */
export const fetchLatestMonthROI = async (): Promise<LatestMonthROI | Error> => {
  try {
    const response = await axios.get<ApiResponse<LatestMonthROI>>(
      `${API_BASE_URL}/api/v1/campaigns/latest-month-roi`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch latest month ROI', error);
    return new Error('Failed to fetch latest month ROI');
  }
};

/**
 * Fetches revenue for the latest month
 * @returns Latest month's revenue data
 */
export const fetchLatestMonthRevenue = async (): Promise<LatestMonthRevenue | Error> => {
  try {
    const response = await axios.get<ApiResponse<LatestMonthRevenue>>(
      `${API_BASE_URL}/api/v1/campaigns/latest-month-revenue`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch latest month revenue', error);
    return new Error('Failed to fetch latest month revenue');
  }
};

/**
 * Fetches prophet prediction data
 * @param fromDate Optional start date (Unix timestamp)
 * @param toDate Optional end date (Unix timestamp)
 * @returns Prophet prediction data
 */
export const fetchProphetPredictions = async (
  fromDate?: number,
  toDate?: number
): Promise<ProphetPredictionData[] | Error> => {
  try {
    const params = new URLSearchParams();
    if (fromDate) params.append('from_date', fromDate.toString());
    if (toDate) params.append('to_date', toDate.toString());

    const response = await axios.get<ProphetPredictionResponse>(
      `${API_BASE_URL}/api/v1/prophet-predictions?${params.toString()}`
    );

    if (response.data.success && response.data.data?.data) {
      return response.data.data.data;
    }
    throw new Error('Invalid response format from prophet predictions API');
  } catch (error) {
    console.error('Failed to fetch prophet predictions', error);
    return new Error('Failed to fetch prophet predictions');
  }
};

/**
 * Fetches monthly data by channel
 * @returns Revenue and ad spend per month per channel
 */
export const fetchMonthlyChannelData = async (): Promise<MonthlyChannelData | Error> => {
  try {
    const response = await axios.get<ApiResponse<MonthlyChannelData>>(
      `${API_BASE_URL}/api/v1/campaigns/monthly-channel-data`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch monthly channel data', error);
    return new Error('Failed to fetch monthly channel data');
  }
};

/**
 * Fetches monthly data by age group
 * @returns Revenue and ad spend per month per age group
 */
export const fetchMonthlyAgeData = async (): Promise<MonthlyAgeData | Error> => {
  try {
    const response = await axios.get<ApiResponse<MonthlyAgeData>>(
      `${API_BASE_URL}/api/v1/campaigns/monthly-age-data`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch monthly age group data', error);
    return new Error('Failed to fetch monthly age group data');
  }
};

/**
 * Fetches monthly data by country
 * @returns Revenue and ad spend per month per country
 */
export const fetchMonthlyCountryData = async (): Promise<MonthlyCountryData | Error> => {
  try {
    const response = await axios.get<ApiResponse<MonthlyCountryData>>(
      `${API_BASE_URL}/api/v1/campaigns/monthly-country-data`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch monthly country data', error);
    return new Error('Failed to fetch monthly country data');
  }
};

/**
 * Fetches data for the latest 12 months
 * @returns Date, revenue and ad spend for the last 12 months
 */
export const fetchLatestTwelveMonths = async (): Promise<LatestTwelveMonthsData | Error> => {
  try {
    const response = await axios.get<ApiResponse<LatestTwelveMonthsData>>(
      `${API_BASE_URL}/api/v1/campaigns/latest-twelve-months`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch latest twelve months data', error);
    return new Error('Failed to fetch latest twelve months data');
  }
};

/**
 * Prophet Pipeline API
 */

/**
 * Triggers the Prophet prediction pipeline
 * @returns Pipeline status message
 */
export const triggerProphetPipeline = async (
  forecastMonths = 4
): Promise<ProphetPipelineResponse | Error> => {
  try {
    const response = await axios.post<ProphetPipelineResponse>(
      `${API_BASE_URL}/api/v1/prophet-pipeline/trigger`,
      { forecast_months: forecastMonths }
    );
    return response.data;
  } catch (error) {
    console.error('Failed to trigger Prophet pipeline', error);
    return new Error('Failed to trigger Prophet pipeline');
  }
};

/**
 * Checks the Prophet prediction pipeline status
 * @returns Current pipeline status
 */
export const checkProphetPipelineStatus = async (): Promise<ProphetPipelineResponse | Error> => {
  try {
    const response = await axios.get<ProphetPipelineResponse>(
      `${API_BASE_URL}/api/v1/prophet-pipeline/status`
    );
    return response.data;
  } catch (error) {
    console.error('Failed to check Prophet pipeline status', error);
    return new Error('Failed to check Prophet pipeline status');
  }
};

/**
 * Fetches databases
 * @returns List of database names
 */
export const fetchDatabases = async (): Promise<DatabaseListResponse | Error> => {
  try {
    const response = await axios.get<ApiResponse<DatabaseListResponse>>(
      `${API_BASE_URL}/api/v1/database`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch databases', error);
    return new Error('Failed to fetch databases');
  }
};

/**
 * Deletes a database
 * @param databaseName Name of the database to delete
 * @returns Success message
 */
export const deleteDatabase = async (
  databaseName: string
): Promise<DatabaseDeleteResponse | Error> => {
  try {
    const response = await axios.post<DatabaseDeleteResponse>(
      `${API_BASE_URL}/api/v1/database/delete`,
      { database_name: databaseName }
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      // Type-safe error handling using the data_types.py structure
      const errorData = error.response.data as {
        error?: {
          message?: string;
          type?: string;
          details?: unknown;
        };
      };

      return new Error(errorData.error?.message ?? 'Failed to delete database');
    }
    return new Error('Failed to delete database');
  }
};

/**
 * Fetches campaign date range information
 * @returns Min and max dates for campaign data as Unix timestamps
 */
export const fetchCampaignDateRange = async (): Promise<
  { min_date: number | null; max_date: number | null } | Error
> => {
  try {
    const response = await axios.get<
      ApiResponse<{ min_date: number | null; max_date: number | null }>
    >(`${API_BASE_URL}/api/v1/campaigns/date-range`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch campaign date range', error);
    return new Error('Failed to fetch campaign date range');
  }
};
