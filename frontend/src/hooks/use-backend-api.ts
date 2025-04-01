import { useState, useCallback } from "react";
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
import * as backendApi from "@/api/backendApi";

// Generic hook state type
interface HookState<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
}

// Database Structure Hook
export const useDbStructure = () => {
  const [state, setState] = useState<HookState<DbStructure>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchStructure = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchDbStructure();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchStructure };
};

// User Hooks
export const useUsers = () => {
  const [state, setState] = useState<HookState<UserData[] | UserData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchUsers = useCallback(async (username?: string) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchUsers(username);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchUsers };
};

export const useAddUser = () => {
  const [state, setState] = useState<HookState<string>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const addUser = useCallback(async (userData: UserData) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.addUser(userData);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, addUser };
};

export const useUserByUsername = (username: string) => {
  const [state, setState] = useState<HookState<UserData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchUser = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchUserByUsername(username);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, [username]);

  return { ...state, fetchUser };
};

export const useUpdateUser = () => {
  const [state, setState] = useState<HookState<string>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const updateUser = useCallback(
    async (username: string, userData: UserData) => {
      setState((prev) => ({ ...prev, isLoading: true }));
      const result = await backendApi.updateUser(username, userData);

      if (result instanceof Error) {
        setState({ data: null, isLoading: false, error: result });
      } else {
        setState({ data: result, isLoading: false, error: null });
      }
    },
    [],
  );

  return { ...state, updateUser };
};

export const useDeleteUser = () => {
  const [state, setState] = useState<HookState<string>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const deleteUser = useCallback(async (username: string) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.deleteUser(username);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, deleteUser };
};

export const usePatchUser = () => {
  const [state, setState] = useState<HookState<string>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const patchUser = useCallback(
    async (username: string, patchData: Partial<UserData>) => {
      setState((prev) => ({ ...prev, isLoading: true }));
      const result = await backendApi.patchUser(username, patchData);

      if (result instanceof Error) {
        setState({ data: null, isLoading: false, error: result });
      } else {
        setState({ data: result, isLoading: false, error: null });
      }
    },
    [],
  );

  return { ...state, patchUser };
};

// Campaign Hooks
export const useCampaignFilterOptions = () => {
  const [state, setState] = useState<HookState<CampaignFilterOptions>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchFilterOptions = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchCampaignFilterOptions();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchFilterOptions };
};

export const useCampaigns = () => {
  const [state, setState] = useState<HookState<FilterResponse>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchCampaigns = useCallback(async (filters: CampaignFilters) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchCampaigns(filters);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchCampaigns };
};

export const useMonthlyPerformance = () => {
  const [state, setState] = useState<HookState<MonthlyPerformanceData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchMonthlyData = useCallback(
    async (filters?: Partial<CampaignFilters>) => {
      setState((prev) => ({ ...prev, isLoading: true }));
      const result = await backendApi.fetchMonthlyPerformanceData(filters);

      if (result instanceof Error) {
        setState({ data: null, isLoading: false, error: result });
      } else {
        setState({ data: result, isLoading: false, error: null });
      }
    },
    [],
  );

  return { ...state, fetchMonthlyData };
};

export const useUpdateMonthlyData = () => {
  const [state, setState] = useState<HookState<MonthlyPerformanceData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const updateMonthly = useCallback(async (updates: MonthlyUpdateData[]) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.updateMonthlyData(updates);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, updateMonthly };
};

export const useCsvUpload = () => {
  const [state, setState] = useState<HookState<CsvUploadResponse>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const uploadCsv = useCallback(async (file: File) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.uploadCsv(file);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, uploadCsv };
};

export const useCostHeatmap = () => {
  const [state, setState] = useState<HookState<backendApi.CostHeatmapData[]>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchHeatmapData = useCallback(
    async (params?: {
      country?: string;
      campaign_id?: string;
      channels?: string[];
    }) => {
      setState((prev) => ({ ...prev, isLoading: true }));
      const result = await backendApi.fetchCostHeatmapData(params);

      if (result instanceof Error) {
        setState({ data: null, isLoading: false, error: result });
      } else {
        setState({ data: result, isLoading: false, error: null });
      }
    },
    [],
  );

  return { ...state, fetchHeatmapData };
};
