import { useState } from "react";
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
  type UserData,
} from "@/types/types";
import * as backendApi from "@/api/backendApi";
import { type CostHeatmapData } from "@/api/backendApi";

// Generic hook for API calls
interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

// User hooks
export const useUsers = () => {
  const [state, setState] = useState<ApiState<UserData[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchUsers = async () => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchUsers();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  return { ...state, fetchUsers };
};

export const useUser = (username: string) => {
  const [state, setState] = useState<ApiState<UserData>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchUser = async () => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchUserByUsername(username);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  const updateUser = async (userData: UserData) => {
    setState({ ...state, loading: true, error: null });
    try {
      const message = await backendApi.updateUser(username, userData);
      if (message) {
        await fetchUser();
      }
      return message;
    } catch (error) {
      setState({ ...state, loading: false, error: error as Error });
      return null;
    }
  };

  const deleteUser = async () => {
    setState({ ...state, loading: true, error: null });
    try {
      const message = await backendApi.deleteUser(username);
      setState({ data: null, loading: false, error: null });
      return message;
    } catch (error) {
      setState({ ...state, loading: false, error: error as Error });
      return null;
    }
  };

  return { ...state, fetchUser, updateUser, deleteUser };
};

export const useAddUser = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const addUser = async (userData: UserData) => {
    setLoading(true);
    setError(null);
    try {
      const message = await backendApi.addUser(userData);
      setLoading(false);
      return message;
    } catch (error) {
      setLoading(false);
      setError(error as Error);
      return null;
    }
  };

  return { addUser, loading, error };
};

// Campaign hooks
export const useCampaignFilterOptions = () => {
  const [state, setState] = useState<ApiState<CampaignFilterOptions>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchOptions = async () => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchCampaignFilterOptions();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  return { ...state, fetchOptions };
};

export const useCampaigns = () => {
  const [state, setState] = useState<ApiState<FilterResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchCampaigns = async (filters: CampaignFilters = {}) => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchCampaigns(filters);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  return { ...state, fetchCampaigns };
};

export const useRevenueData = () => {
  const [state, setState] = useState<ApiState<RevenueData[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchRevenueData = async () => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchRevenueData();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  return { ...state, fetchRevenueData };
};

export const useMonthlyPerformance = () => {
  const [state, setState] = useState<ApiState<MonthlyPerformanceData>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchMonthlyPerformance = async (
    filters?: Partial<CampaignFilters>,
  ) => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchMonthlyPerformanceData(filters);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  const updateMonthlyData = async (updates: MonthlyUpdateData[]) => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.updateMonthlyData(updates);
      setState({ data, loading: false, error: null });
      return data;
    } catch (error) {
      setState({ ...state, loading: false, error: error as Error });
      return null;
    }
  };

  return { ...state, fetchMonthlyPerformance, updateMonthlyData };
};

export const useChannelRoi = () => {
  const [state, setState] = useState<ApiState<ChannelRoi[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchChannelRoi = async () => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchChannelRoi();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  return { ...state, fetchChannelRoi };
};

export const useAgeGroupRoi = () => {
  const [state, setState] = useState<ApiState<AgeGroupRoi[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchAgeGroupRoi = async () => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchAgeGroupRoi();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  return { ...state, fetchAgeGroupRoi };
};

export const useCsvUpload = () => {
  const [state, setState] = useState<ApiState<CsvUploadResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const uploadCsv = async (file: File) => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.uploadCsv(file);
      setState({ data, loading: false, error: null });
      return data;
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
      return null;
    }
  };

  return { ...state, uploadCsv };
};

export const useCostHeatmap = () => {
  const [state, setState] = useState<ApiState<CostHeatmapData[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchCostHeatmapData = async (params?: {
    country?: string;
    campaign_id?: string;
    channels?: string[];
  }) => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchCostHeatmapData(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  return { ...state, fetchCostHeatmapData };
};

export const useDbStructure = () => {
  const [state, setState] = useState<ApiState<DbStructure>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchDbStructure = async () => {
    setState({ ...state, loading: true, error: null });
    try {
      const data = await backendApi.fetchDbStructure();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
    }
  };

  return { ...state, fetchDbStructure };
};
