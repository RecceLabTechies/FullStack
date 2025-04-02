/**
 * This module contains all API calls to the backend server.
 * It provides functions for interacting with users, campaigns, and database operations.
 * All functions handle errors gracefully and return either the expected data or an Error object.
 */
import {
  type CampaignFilterOptions,
  type CampaignFilters,
  type ChannelContributionData,
  type CostMetricsHeatmapData,
  type CsvUploadResponse,
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
const API_BASE_URL = 'http://localhost:5001';

/**
 * Database Structure API Section
 */

/**
 * Fetches the current database structure from the backend
 * @returns Promise resolving to DbStructure containing tables and relationships
 */
export const fetchDbStructure = async (): Promise<DbStructure | Error> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/database/structure`);
    const apiResponse = response.data as {
      data: DbStructure;
      status: number;
      success: boolean;
    };
    return apiResponse.data;
  } catch (error) {
    console.error('Failed to fetch database structure', error);
    return new Error('Failed to fetch database structure');
  }
};

/**
 * User Management API Section
 */

/**
 * Fetches users from the backend
 * @param username Optional - If provided, fetches a specific user
 * @returns Promise resolving to either a single user or array of users
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
 * Creates a new user in the system
 * @param user User data object containing all required user information
 * @returns Promise resolving to a success message or error
 */
export const addUser = async (user: UserData): Promise<string | Error> => {
  try {
    interface AddUserResponse {
      message: string;
      id?: string;
    }
    const response = await axios.post<AddUserResponse>(`${API_BASE_URL}/api/v1/users`, user);
    return response.data.message;
  } catch (error) {
    console.error('Failed to add user', error);
    return new Error('Failed to add user');
  }
};

/**
 * Retrieves a specific user by their username
 * @param username The unique username to search for
 * @returns Promise resolving to the user data or error
 */
export const fetchUserByUsername = async (username: string): Promise<UserData | Error> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/users/${username}`);
    return response.data as UserData;
  } catch (error) {
    console.error('Failed to fetch user by username', error);
    return new Error('Failed to fetch user by username');
  }
};

/**
 * Updates all fields of an existing user
 * @param username The username of the user to update
 * @param userData Complete user data object with new values
 * @returns Promise resolving to a success message or error
 */
export const updateUser = async (username: string, userData: UserData): Promise<string | Error> => {
  try {
    interface UpdateUserResponse {
      message: string;
    }
    const response = await axios.put<UpdateUserResponse>(
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
 * Removes a user from the system
 * @param username The username of the user to delete
 * @returns Promise resolving to a success message or error
 */
export const deleteUser = async (username: string): Promise<string | Error> => {
  try {
    interface DeleteUserResponse {
      message: string;
    }
    const response = await axios.delete<DeleteUserResponse>(
      `${API_BASE_URL}/api/v1/users/${username}`
    );
    return response.data.message;
  } catch (error) {
    console.error('Failed to delete user', error);
    return new Error('Failed to delete user');
  }
};

/**
 * Partially updates a user's information
 * @param username The username of the user to update
 * @param patchData Object containing only the fields to be updated
 * @returns Promise resolving to a success message or error
 */
export const patchUser = async (
  username: string,
  patchData: Partial<UserData>
): Promise<string | Error> => {
  try {
    interface PatchUserResponse {
      message: string;
    }
    const response = await axios.patch<PatchUserResponse>(
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
 * Campaign Management API Section
 */

/**
 * Retrieves available filter options for campaigns
 * @returns Promise resolving to campaign filter options or error
 */
export const fetchCampaignFilterOptions = async (): Promise<CampaignFilterOptions | Error> => {
  try {
    const response = await axios.get<{
      data: CampaignFilterOptions;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/filter-options`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch campaign filter options', error);
    return new Error('Failed to fetch campaign filter options');
  }
};

/**
 * Fetches filtered campaign data based on provided criteria
 * @param filters Object containing filter parameters for campaigns
 * @returns Promise resolving to filtered campaign data or error
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
 * Retrieves aggregated monthly performance data for campaigns
 * @param filters Filter criteria for the monthly aggregation
 * @returns Promise resolving to monthly performance metrics or error
 */
export const fetchMonthlyAggregatedData = async (
  filters: CampaignFilters
): Promise<MonthlyPerformanceData | Error> => {
  try {
    const response = await axios.post<{
      data: MonthlyPerformanceData;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/monthly-aggregated`, filters);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch monthly aggregated data', error);
    return new Error('Failed to fetch monthly aggregated data');
  }
};

/**
 * Data Import API Section
 */

/**
 * Uploads and processes a CSV file for data import
 * @param file The CSV file to be uploaded
 * @returns Promise resolving to upload response containing processing results
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
 * Analytics API Section
 */

/**
 * Fetches channel contribution data for various metrics over the latest 3 months
 * @returns Promise resolving to channel contribution data or error
 */
export const fetchChannelContribution = async (): Promise<ChannelContributionData | Error> => {
  try {
    const response = await axios.get<{
      data: ChannelContributionData;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/channel-contribution`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch channel contribution data', error);
    return new Error('Failed to fetch channel contribution data');
  }
};

/**
 * Fetches cost metrics heatmap data showing different cost metrics by channel
 * @returns Promise resolving to cost metrics heatmap data or error
 */
export const fetchCostMetricsHeatmap = async (): Promise<CostMetricsHeatmapData | Error> => {
  try {
    const response = await axios.get<{
      data: CostMetricsHeatmapData;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/cost-metrics-heatmap`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch cost metrics heatmap data', error);
    return new Error('Failed to fetch cost metrics heatmap data');
  }
};

/**
 * Fetches ROI (Return on Investment) for the latest month
 * @returns Promise resolving to latest month's ROI data or error
 */
export const fetchLatestMonthROI = async (): Promise<LatestMonthROI | Error> => {
  try {
    const response = await axios.get<{
      data: LatestMonthROI;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/latest-month-roi`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch latest month ROI', error);
    return new Error('Failed to fetch latest month ROI');
  }
};

/**
 * Fetches total revenue for the latest month
 * @returns Promise resolving to latest month's revenue data or error
 */
export const fetchLatestMonthRevenue = async (): Promise<LatestMonthRevenue | Error> => {
  try {
    const response = await axios.get<{
      data: LatestMonthRevenue;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/latest-month-revenue`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch latest month revenue', error);
    return new Error('Failed to fetch latest month revenue');
  }
};

/**
 * Fetches prophet prediction data, optionally filtered by date range.
 * @param fromDate Optional start date as Unix timestamp
 * @param toDate Optional end date as Unix timestamp
 * @returns Promise resolving to prophet prediction data or error
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
 * Fetches monthly data aggregated by channel for charting purposes.
 * Returns revenue and ad spend metrics per month per channel.
 * @returns Promise resolving to monthly channel data or error
 */
export const fetchMonthlyChannelData = async (): Promise<MonthlyChannelData | Error> => {
  try {
    const response = await axios.get<{
      data: MonthlyChannelData;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/monthly-channel-data`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch monthly channel data', error);
    return new Error('Failed to fetch monthly channel data');
  }
};

/**
 * Fetches monthly data aggregated by age group for charting purposes.
 * Returns revenue and ad spend metrics per month per age group.
 * @returns Promise resolving to monthly age group data or error
 */
export const fetchMonthlyAgeData = async (): Promise<MonthlyAgeData | Error> => {
  try {
    const response = await axios.get<{
      data: MonthlyAgeData;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/monthly-age-data`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch monthly age group data', error);
    return new Error('Failed to fetch monthly age group data');
  }
};

/**
 * Fetches monthly data aggregated by country for charting purposes.
 * Returns revenue and ad spend metrics per month per country.
 * @returns Promise resolving to monthly country data or error
 */
export const fetchMonthlyCountryData = async (): Promise<MonthlyCountryData | Error> => {
  try {
    const response = await axios.get<{
      data: MonthlyCountryData;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/monthly-country-data`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch monthly country data', error);
    return new Error('Failed to fetch monthly country data');
  }
};

/**
 * Fetches the latest 12 months of aggregated data with date, revenue and ad spend.
 * @returns Promise resolving to latest twelve months data or error
 */
export const fetchLatestTwelveMonths = async (): Promise<LatestTwelveMonthsData | Error> => {
  try {
    const response = await axios.get<{
      data: LatestTwelveMonthsData;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/latest-twelve-months`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch latest twelve months data', error);
    return new Error('Failed to fetch latest twelve months data');
  }
};

/**
 * Prophet Pipeline API Section
 */

/**
 * Triggers the Prophet prediction pipeline to run in the background.
 * The pipeline will fetch data from campaign_performance collection,
 * run predictions, and store results in prophet_predictions collection.
 * @returns Promise resolving to status message or error
 */
export const triggerProphetPipeline = async (): Promise<ProphetPipelineResponse | Error> => {
  try {
    const response = await axios.post<ProphetPipelineResponse>(
      `${API_BASE_URL}/api/v1/prophet-pipeline/trigger`
    );
    return response.data;
  } catch (error) {
    console.error('Failed to trigger Prophet pipeline', error);
    return new Error('Failed to trigger Prophet pipeline');
  }
};

/**
 * Checks the current status of the Prophet prediction pipeline.
 * @returns Promise resolving to pipeline status or error
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
