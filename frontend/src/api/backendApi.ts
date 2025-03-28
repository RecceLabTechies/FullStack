import {
  type AgeGroupRoi,
  type CampaignFilterOptions,
  type CampaignFilters,
  type ChannelRoi,
  type CsvUploadResponse,
  type DbStructure,
  type FilterResponse,
  type MonthlyPerformanceData,
  type MonthlyUpdateData,
  type RevenueData,
  type RevenuePastMonth,
  type RoiPastMonth,
  type UserData,
} from "@/types/types";
import axios, { AxiosResponse } from "axios";

const API_BASE_URL = "http://localhost:5001";

export const fetchDbStructure = async (): Promise<DbStructure | null> => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/database-structures`,
    );
    return response.data as DbStructure;
  } catch (error) {
    console.error("Failed to fetch database structure", error);
    return null;
  }
};

// User-related API calls
export const fetchUsers = async (): Promise<UserData[] | null> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/users`);
    return response.data as UserData[];
  } catch (error) {
    console.error("Failed to fetch users", error);
    return null;
  }
};

export const addUser = async (user: UserData): Promise<string | null> => {
  try {
    interface AddUserResponse {
      message: string;
      id?: string;
    }
    const response = await axios.post<AddUserResponse>(
      `${API_BASE_URL}/api/users`,
      user,
    );
    return response.data.message;
  } catch (error) {
    console.error("Failed to add user", error);
    return null;
  }
};

export const fetchUserByUsername = async (
  username: string,
): Promise<UserData | null> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/users/${username}`);
    return response.data as UserData;
  } catch (error) {
    console.error("Failed to fetch user by username", error);
    return null;
  }
};

export const updateUser = async (
  username: string,
  userData: UserData,
): Promise<string | null> => {
  try {
    interface UpdateUserResponse {
      message: string;
    }
    const response = await axios.put<UpdateUserResponse>(
      `${API_BASE_URL}/api/users/${username}`,
      userData,
    );
    return response.data.message;
  } catch (error) {
    console.error("Failed to update user", error);
    return null;
  }
};

export const deleteUser = async (username: string): Promise<string | null> => {
  try {
    interface DeleteUserResponse {
      message: string;
    }
    const response = await axios.delete<DeleteUserResponse>(
      `${API_BASE_URL}/api/users/${username}`,
    );
    return response.data.message;
  } catch (error) {
    console.error("Failed to delete user", error);
    return null;
  }
};

export const patchUser = async (
  username: string,
  patchData: Partial<UserData>,
): Promise<string | null> => {
  try {
    interface PatchUserResponse {
      message: string;
    }
    const response = await axios.patch<PatchUserResponse>(
      `${API_BASE_URL}/api/users/${username}`,
      patchData,
    );
    return response.data.message;
  } catch (error) {
    console.error("Failed to patch user", error);
    return null;
  }
};

// Campaign-related API calls
export const fetchCampaignFilterOptions =
  async (): Promise<CampaignFilterOptions | null> => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/campaigns/filter-options`,
      );
      return response.data as CampaignFilterOptions;
    } catch (error) {
      console.error("Failed to fetch campaign filter options", error);
      return null;
    }
  };

export const fetchCampaigns = async (
  filters: CampaignFilters,
): Promise<FilterResponse | null> => {
  try {
    // Map frontend filter names to backend expected format
    const apiFilters: Record<string, unknown> = { ...filters };

    // Convert to query parameters for GET request
    if (Object.keys(filters).length > 0) {
      const response = await axios.get<FilterResponse>(
        `${API_BASE_URL}/api/v1/campaigns`,
        { params: apiFilters },
      );
      return response.data;
    } else {
      const response = await axios.get<FilterResponse>(
        `${API_BASE_URL}/api/v1/campaigns`,
      );
      return response.data;
    }
  } catch (error) {
    console.error("Failed to fetch campaign data", error);
    return null;
  }
};

export const fetchRevenueData = async (): Promise<RevenueData[] | null> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/revenues`);
    return response.data as RevenueData[];
  } catch (error) {
    console.error("Failed to fetch revenue data", error);
    return null;
  }
};

export const fetchMonthlyPerformanceData = async (
  filters?: Partial<CampaignFilters>,
): Promise<MonthlyPerformanceData | null> => {
  try {
    const response = await axios.get<MonthlyPerformanceData>(
      `${API_BASE_URL}/api/v1/chart/monthly-performance`,
      { params: filters },
    );
    return response.data;
  } catch (error) {
    console.error("Failed to fetch monthly performance data", error);
    return null;
  }
};

export const updateMonthlyData = async (
  updates: MonthlyUpdateData[],
): Promise<MonthlyPerformanceData | null> => {
  try {
    interface UpdateMonthlyResponse {
      message: string;
      months: string[];
      revenue: number[];
      ad_spend: number[];
      roi: number[];
    }

    const response = await axios.post<UpdateMonthlyResponse>(
      `${API_BASE_URL}/api/v1/chart/update-monthly-data`,
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
    return null;
  }
};

export const uploadCsv = async (
  file: File,
): Promise<CsvUploadResponse | null> => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post<CsvUploadResponse>(
      `${API_BASE_URL}/api/v1/csv-imports`,
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
    return null;
  }
};

export const fetchChannelRoi = async (): Promise<ChannelRoi[] | null> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/channel-roi`);
    return response.data as ChannelRoi[];
  } catch (error) {
    console.error("Failed to fetch channel ROI data", error);
    return null;
  }
};

export const fetchAgeGroupRoi = async (): Promise<AgeGroupRoi[] | null> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/age-group-roi`);
    return response.data as AgeGroupRoi[];
  } catch (error) {
    console.error("Failed to fetch age group ROI data", error);
    return null;
  }
};

export const fetchRevenuePastMonth = async (): Promise<number | null> => {
  try {
    const response = await axios.get<RevenuePastMonth>(
      `${API_BASE_URL}/api/v1/revenue-past-month`,
    );
    return response.data.revenue;
  } catch (error) {
    console.error("Failed to fetch past month revenue", error);
    return null;
  }
};

export const fetchRoiPastMonth = async (): Promise<number | null> => {
  try {
    const response = await axios.get<RoiPastMonth>(
      `${API_BASE_URL}/api/v1/roi-past-month`,
    );
    return response.data.roi;
  } catch (error) {
    console.error("Failed to fetch past month ROI", error);
    return null;
  }
};

export const getDateTypes = async (): Promise<{
  value: unknown;
  type: string;
} | null> => {
  try {
    interface DateTypeResponse {
      value: unknown;
      type: string;
    }

    const response = await axios.get<DateTypeResponse>(
      `${API_BASE_URL}/api/v1/date-types`,
    );
    return response.data;
  } catch (error) {
    console.error("Failed to get date types", error);
    return null;
  }
};

type FilteredData = {
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
};

// Yuting Function

export const fetchFilteredData = async ({
  channels,
  ageGroups,
  countries,
  from,
  to,
}: {
  channels?: string[];
  ageGroups?: string[];
  countries?: string[];
  from?: string;
  to?: string;
}): Promise<FilteredData[]> => {
  const response: AxiosResponse<FilteredData[]> = await axios.post(
    "http://localhost:5001/api/filter-data",
    {
      channels,
      ageGroups,
      countries,
      from,
      to,
    },
  );

  return response.data;
};

// data for cost heatmap
export interface CostHeatmapData {
  channel: string;
  costPerLead: number;
  costPerView: number;
  costPerAccount: number;
}

export const fetchCostHeatmapData = async (): Promise<
  CostHeatmapData[] | null
> => {
  try {
    const response = await axios.get(
      "http://localhost:5001/api/get-cost-heatmap-data",
    );
    return response.data as CostHeatmapData[];
  } catch (error) {
    console.error("Failed to fetch cost heatmap data", error);
    return null;
  }
};
