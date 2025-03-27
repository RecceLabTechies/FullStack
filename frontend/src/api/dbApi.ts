import { type CampaignData, type UserData } from "@/types/types";
import axios from "axios";

export interface DbStructure {
  test_database: {
    campaign_data_mock: CampaignData[];
  };
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
