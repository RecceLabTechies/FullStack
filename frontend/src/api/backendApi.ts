import {
  type CampaignFilterOptions,
  type CampaignFilters,
  type CsvUploadResponse,
  type DbStructure,
  type FilterResponse,
  type MonthlyPerformanceData,
  type MonthlyUpdateData,
  type UserData,
} from "@/types/types";
import axios from "axios";

const API_BASE_URL = "http://localhost:5001";

// Database Structure API
export const fetchDbStructure = async (): Promise<DbStructure | Error> => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/database/structure`,
    );
    const apiResponse = response.data as {
      data: DbStructure;
      status: number;
      success: boolean;
    };
    return apiResponse.data;
  } catch (error) {
    console.error("Failed to fetch database structure", error);
    return new Error("Failed to fetch database structure");
  }
};

// User-related API calls
export const fetchUsers = async (
  username?: string,
): Promise<UserData[] | UserData | Error> => {
  try {
    const url = username
      ? `${API_BASE_URL}/api/v1/users?username=${username}`
      : `${API_BASE_URL}/api/v1/users`;
    const response = await axios.get<UserData[] | UserData>(url);
    return response.data;
  } catch (error) {
    console.error("Failed to fetch users", error);
    return new Error("Failed to fetch users");
  }
};

export const addUser = async (user: UserData): Promise<string | Error> => {
  try {
    interface AddUserResponse {
      message: string;
      id?: string;
    }
    const response = await axios.post<AddUserResponse>(
      `${API_BASE_URL}/api/v1/users`,
      user,
    );
    return response.data.message;
  } catch (error) {
    console.error("Failed to add user", error);
    return new Error("Failed to add user");
  }
};

export const fetchUserByUsername = async (
  username: string,
): Promise<UserData | Error> => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/users/${username}`,
    );
    return response.data as UserData;
  } catch (error) {
    console.error("Failed to fetch user by username", error);
    return new Error("Failed to fetch user by username");
  }
};

export const updateUser = async (
  username: string,
  userData: UserData,
): Promise<string | Error> => {
  try {
    interface UpdateUserResponse {
      message: string;
    }
    const response = await axios.put<UpdateUserResponse>(
      `${API_BASE_URL}/api/v1/users/${username}`,
      userData,
    );
    return response.data.message;
  } catch (error) {
    console.error("Failed to update user", error);
    return new Error("Failed to update user");
  }
};

export const deleteUser = async (username: string): Promise<string | Error> => {
  try {
    interface DeleteUserResponse {
      message: string;
    }
    const response = await axios.delete<DeleteUserResponse>(
      `${API_BASE_URL}/api/v1/users/${username}`,
    );
    return response.data.message;
  } catch (error) {
    console.error("Failed to delete user", error);
    return new Error("Failed to delete user");
  }
};

export const patchUser = async (
  username: string,
  patchData: Partial<UserData>,
): Promise<string | Error> => {
  try {
    interface PatchUserResponse {
      message: string;
    }
    const response = await axios.patch<PatchUserResponse>(
      `${API_BASE_URL}/api/v1/users/${username}`,
      patchData,
    );
    return response.data.message;
  } catch (error) {
    console.error("Failed to patch user", error);
    return new Error("Failed to patch user");
  }
};

// Campaign-related API calls
export const fetchCampaignFilterOptions = async (): Promise<
  CampaignFilterOptions | Error
> => {
  try {
    const response = await axios.get<{
      data: CampaignFilterOptions;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/filter-options`);
    return response.data.data;
  } catch (error) {
    console.error("Failed to fetch campaign filter options", error);
    return new Error("Failed to fetch campaign filter options");
  }
};

export const fetchCampaigns = async (
  filters: CampaignFilters,
): Promise<FilterResponse | Error> => {
  try {
    const response = await axios.get<FilterResponse>(
      `${API_BASE_URL}/api/v1/campaigns`,
      { params: filters },
    );
    return response.data;
  } catch (error) {
    console.error("Failed to fetch campaign data", error);
    return new Error("Failed to fetch campaign data");
  }
};

export const fetchMonthlyPerformanceData = async (
  filters?: Partial<CampaignFilters>,
): Promise<MonthlyPerformanceData | Error> => {
  try {
    const response = await axios.get<{
      data: MonthlyPerformanceData;
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/monthly-performance`, {
      params: filters,
    });
    return response.data.data;
  } catch (error) {
    console.error("Failed to fetch monthly performance data", error);
    return new Error("Failed to fetch monthly performance data");
  }
};

export const updateMonthlyData = async (
  updates: MonthlyUpdateData[],
): Promise<MonthlyPerformanceData | Error> => {
  try {
    interface UpdateMonthlyResponse {
      message: string;
      months: string[];
      revenue: number[];
      ad_spend: number[];
      roi: number[];
    }

    const response = await axios.post<UpdateMonthlyResponse>(
      `${API_BASE_URL}/api/v1/campaigns/monthly-data`,
      { updates },
    );

    return {
      months: response.data.months,
      revenue: response.data.revenue,
      ad_spend: response.data.ad_spend,
      roi: response.data.roi,
    };
  } catch (error) {
    console.error("Failed to update monthly data", error);
    return new Error("Failed to update monthly data");
  }
};

// CSV Import API
export const uploadCsv = async (
  file: File,
): Promise<CsvUploadResponse | Error> => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post<CsvUploadResponse>(
      `${API_BASE_URL}/api/v1/imports/csv`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );
    return response.data;
  } catch (error) {
    console.error("Failed to upload CSV", error);
    return new Error("Failed to upload CSV");
  }
};

// Cost Heatmap API
export interface CostHeatmapData {
  channel: string;
  costPerLead: number;
  costPerView: number;
  costPerAccount: number;
}

export const fetchCostHeatmapData = async (params?: {
  country?: string;
  campaign_id?: string;
  channels?: string[];
}): Promise<CostHeatmapData[] | Error> => {
  try {
    const response = await axios.get<{
      data: CostHeatmapData[];
      status: number;
      success: boolean;
    }>(`${API_BASE_URL}/api/v1/campaigns/cost-heatmap`, {
      params,
    });
    return response.data.data;
  } catch (error) {
    console.error("Failed to fetch cost heatmap data", error);
    return new Error("Failed to fetch cost heatmap data");
  }
};
