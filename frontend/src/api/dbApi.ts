import { type AdCampaignData } from "@/types/adCampaignTypes";
import axios from "axios";
import type { AxiosResponse } from "axios";

export interface DbStructure {
  test_database: {
    campaign_data_mock: AdCampaignData[];
  };
}

export interface User {
  username: string;
  email: string;
  role: string;
  company: string;
  password: string;
  chart_access: boolean;
  report_generation_access: boolean;
  user_management_access: boolean;
}

export const fetchDbStructure = async (): Promise<DbStructure | null> => {
  try {
    const response = await axios.get("http://localhost:5001/api/db-structure");
    return response.data as DbStructure;
  } catch (error) {
    console.error("Failed to fetch database structure", error);
    return null;
  }
};

export const fetchUsers = async (): Promise<User[] | null> => {
  try {
    const response = await axios.get("http://localhost:5001/api/users");
    return response.data as User[];
  } catch (error) {
    console.error("Failed to fetch users", error);
    return null;
  }
};

export const addUser = async (user: User): Promise<string | null> => {
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
): Promise<User | null> => {
  try {
    const response = await axios.get(
      `http://localhost:5001/api/user?username=${username}`,
    );
    return response.data as User;
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

export const fetchDataSynthFilters = async (): Promise<DataSynthFilters | null> => {
  try {
    const response = await axios.get("http://localhost:5001/api/data_synth_22mar/filters");
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
  const response: AxiosResponse<FilteredData[]> = await axios.post("http://localhost:5001/api/filter-data", {
    channels,
    ageGroups,
    countries,
    from,
    to,
  });

  return response.data;
};