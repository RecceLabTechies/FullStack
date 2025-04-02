import { useCallback, useState } from 'react';

import * as backendApi from '@/api/backendApi';
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
  type ProphetPredictionData,
  type UserData,
} from '@/types/types';

// Generic hook state type that provides loading, error, and data states
interface HookState<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Hook to fetch the database structure.
 * Returns the database schema and table information.
 */
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

/**
 * Hook to fetch users from the backend.
 * Can fetch all users or a specific user by username.
 */
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

/**
 * Hook to add a new user to the system.
 * Takes UserData object and creates a new user record.
 */
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

/**
 * Hook to fetch a specific user's details by their username.
 * Returns detailed information for a single user.
 */
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

/**
 * Hook to update an existing user's information.
 * Takes a username and updated UserData to modify the user record.
 */
export const useUpdateUser = () => {
  const [state, setState] = useState<HookState<string>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const updateUser = useCallback(async (username: string, userData: UserData) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.updateUser(username, userData);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, updateUser };
};

/**
 * Hook to delete a user from the system.
 * Removes a user record by their username.
 */
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

/**
 * Hook to partially update a user's information.
 * Allows updating specific fields of a user record without affecting others.
 */
export const usePatchUser = () => {
  const [state, setState] = useState<HookState<string>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const patchUser = useCallback(async (username: string, patchData: Partial<UserData>) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.patchUser(username, patchData);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, patchUser };
};

/**
 * Hook to fetch available campaign filter options.
 * Returns possible values for filtering campaigns (e.g., categories, statuses).
 */
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

/**
 * Hook to fetch campaigns based on filter criteria.
 * Makes a POST request to fetch filtered campaign data based on provided filter parameters.
 * The filters are sent in the request body as JSON.
 */
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

/**
 * Hook to handle CSV file uploads.
 * Processes CSV files and returns upload response with success/failure details.
 */
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

/**
 * Hook to fetch monthly aggregated campaign data.
 * Returns monthly revenue, ad spend, and ROI data based on campaign filters.
 */
export const useMonthlyAggregatedData = () => {
  const [state, setState] = useState<HookState<MonthlyPerformanceData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchMonthlyData = useCallback(async (filters: CampaignFilters) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchMonthlyAggregatedData(filters);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchMonthlyData };
};

/**
 * Hook to fetch channel contribution data for the stacked column chart.
 * Returns percentage contribution of each channel to different metrics (spending, views, etc.)
 * Uses data from the latest 3 months.
 */
export const useChannelContribution = () => {
  const [state, setState] = useState<HookState<ChannelContributionData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchChannelContribution = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchChannelContribution();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchChannelContribution };
};

/**
 * Hook to fetch cost metrics heatmap data.
 * Returns cost per lead, cost per view, and cost per new account metrics by channel
 * for generating a heatmap visualization.
 */
export const useCostMetricsHeatmap = () => {
  const [state, setState] = useState<HookState<CostMetricsHeatmapData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchCostMetricsHeatmap = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchCostMetricsHeatmap();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchCostMetricsHeatmap };
};

/**
 * Hook to fetch the latest month's ROI (Return on Investment).
 * Returns ROI percentage, month, and year.
 */
export const useLatestMonthROI = () => {
  const [state, setState] = useState<HookState<LatestMonthROI>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchLatestMonthROI = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchLatestMonthROI();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchLatestMonthROI };
};

/**
 * Hook to fetch the latest month's total revenue.
 * Returns revenue amount, month, and year.
 */
export const useLatestMonthRevenue = () => {
  const [state, setState] = useState<HookState<LatestMonthRevenue>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchLatestMonthRevenue = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchLatestMonthRevenue();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchLatestMonthRevenue };
};

/**
 * Hook to fetch prophet prediction data.
 * Returns data optionally filtered by date range.
 */
export const useProphetPredictions = () => {
  const [state, setState] = useState<HookState<ProphetPredictionData[]>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchPredictions = useCallback(async (fromDate?: number, toDate?: number) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchProphetPredictions(fromDate, toDate);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchPredictions };
};

/**
 * Hook to fetch monthly data aggregated by channel for charting purposes.
 * Returns revenue and ad spend metrics per month per channel.
 */
export const useMonthlyChannelData = () => {
  const [state, setState] = useState<HookState<MonthlyChannelData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchMonthlyChannelData = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchMonthlyChannelData();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchMonthlyChannelData };
};

/**
 * Hook to fetch monthly data aggregated by age group for charting purposes.
 * Returns revenue and ad spend metrics per month per age group.
 */
export const useMonthlyAgeData = () => {
  const [state, setState] = useState<HookState<MonthlyAgeData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchMonthlyAgeData = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchMonthlyAgeData();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchMonthlyAgeData };
};

/**
 * Hook to fetch monthly data aggregated by country for charting purposes.
 * Returns revenue and ad spend metrics per month per country.
 */
export const useMonthlyCountryData = () => {
  const [state, setState] = useState<HookState<MonthlyCountryData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchMonthlyCountryData = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchMonthlyCountryData();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchMonthlyCountryData };
};

/**
 * Hook to fetch the latest 12 months of aggregated data.
 * Returns date, revenue and ad spend for each month.
 */
export const useLatestTwelveMonths = () => {
  const [state, setState] = useState<HookState<LatestTwelveMonthsData>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const fetchLatestTwelveMonths = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchLatestTwelveMonths();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, fetchLatestTwelveMonths };
};
