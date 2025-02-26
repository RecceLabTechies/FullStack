import axios from "axios";
import { type AdCampaignData } from "@/types/adCampaignTypes";

interface DbStructure {
  test_database: {
    campaign_data_mock: AdCampaignData[];
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
