import { type CampaignData, type UserData } from "@/types/types";
import type { AxiosResponse } from "axios";
import axios from "axios";

export interface DbStructure {
  test_database: {
    campaign_data_mock: CampaignData[];
  };
}

export const fetchDbStructure = async (): Promise<DbStructure | null> => {
  try {
    const response = await axios.get(
      "http://localhost:5001/api/v1/database-structures",
    );
    return response.data as DbStructure;
  } catch (error) {
    console.error("Failed to fetch database structure", error);
    return null;
  }
};

export const fetchUsers = async (): Promise<UserData[] | null> => {
  try {
    const response = await axios.get("http://localhost:5001/api/users");
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
    }
    const response = await axios.post<AddUserResponse>(
      "http://localhost:5001/api/users",
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
    const response = await axios.get(
      `http://localhost:5001/api/user?username=${username}`,
    );
    return response.data as UserData;
  } catch (error) {
    console.error("Failed to fetch user by username", error);
    return null;
  }
};

export interface DataSynthFilters {
  countries: string[];
  age_groups: string[];
  channels: string[];
}

export const fetchDataSynthFilters =
  async (): Promise<DataSynthFilters | null> => {
    try {
      const response = await axios.get(
        "http://localhost:5001/api/v1/campaigns/filter-options",
      );
      return response.data as DataSynthFilters;
    } catch (error) {
      console.error("Failed to fetch datasynth filters", error);
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
    "http://localhost:5001/api/v1/campaigns",
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

export interface RevenueData {
  date: string;
  revenue: number;
}

export const fetchRevenueData = async (): Promise<RevenueData[] | null> => {
  try {
    const response = await axios.get("http://localhost:5001/api/v1/revenues");
    return response.data as RevenueData[];
  } catch (error) {
    console.error("Failed to fetch revenue data", error);
    return null;
  }
};

export interface CsvUploadResponse {
  message: string;
  count: number;
  collection: string;
}

export const uploadCsv = async (
  file: File,
): Promise<CsvUploadResponse | null> => {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post<CsvUploadResponse>(
      "http://localhost:5001/api/v1/csv-imports",
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
