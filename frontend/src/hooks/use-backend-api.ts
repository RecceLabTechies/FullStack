/**
 * This module provides React hooks for interacting with the backend API.
 * It incudes hooks for managing users, campaigns, analytics, and data processing.
 * Each hook handles its own state management and error handling.
 */
import { useCallback, useState } from 'react';

import * as backendApi from '@/api/backendApi';
import {
  type CampaignFilterOptions,
  type CampaignFilters,
  type ChannelContributionData,
  type CostMetricsHeatmapData,
  type CsvUploadResponse,
  type DatabaseDeleteResponse,
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
  type UserData,
} from '@/types/types';

/**
 * Generic state interface for all hooks
 * Provides consistent state management across different data types
 */
interface HookState<T> {
  /** The data returned from the API */
  data: T | null;
  /** Loading state indicator */
  isLoading: boolean;
  /** Error object if the operation failed */
  error: Error | null;
}

/**
 * Initial state factory for hooks
 * Creates a fresh state object with default values
 */
const createInitialState = <T>(): HookState<T> => ({
  data: null,
  isLoading: false,
  error: null,
});

/**
 * Generic state update helper for successful API calls
 */
const handleSuccess = <T>(
  setState: React.Dispatch<React.SetStateAction<HookState<T>>>,
  data: T
) => {
  setState({ data, isLoading: false, error: null });
};

/**
 * Generic state update helper for failed API calls
 */
const handleError = <T>(
  setState: React.Dispatch<React.SetStateAction<HookState<T>>>,
  error: Error
) => {
  setState({ data: null, isLoading: false, error });
};

/**
 * Database Structure API Hooks
 */

/**
 * Hook for fetching the database structure
 *
 * @example
 * ```tsx
 * function DatabaseViewer() {
 *   const { data, isLoading, error, fetchStructure } = useDbStructure();
 *
 *   useEffect(() => {
 *     void fetchStructure();
 *   }, [fetchStructure]);
 *
 *   if (isLoading) return <Loading />;
 *   if (error) return <Error message={error.message} />;
 *   if (!data) return null;
 *
 *   return <DatabaseStructure data={data} />;
 * }
 */
export const useDbStructure = () => {
  const [state, setState] = useState<HookState<DbStructure>>(createInitialState());

  const fetchStructure = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchDbStructure();

    if (result instanceof Error) {
      handleError(setState, result);
    } else {
      handleSuccess(setState, result);
    }
  }, []);

  return { ...state, fetchStructure };
};

/**
 * User Management API Hooks
 */

/**
 * Hook for fetching users
 * Can retrieve all users or filter by username
 *
 * @example
 * ```tsx
 * function UserList() {
 *   const { data, isLoading, fetchUsers } = useUsers();
 *
 *   useEffect(() => {
 *     void fetchUsers();
 *   }, [fetchUsers]);
 *
 *   return isLoading ? <Loading /> : <UserTable users={data || []} />;
 */
export const useUsers = () => {
  const [state, setState] = useState<HookState<UserData[] | UserData>>(createInitialState());

  const fetchUsers = useCallback(async (username?: string) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchUsers(username);

    if (result instanceof Error) {
      handleError(setState, result);
    } else {
      handleSuccess(setState, result);
    }
  }, []);

  return { ...state, fetchUsers };
};

/**
 * Hook for adding new users
 *
 * @example
 * ```tsx
 * function AddUserForm() {
 *   const { isLoading, error, addUser } = useAddUser();
 *
 *   const handleSubmit = async (userData: UserData) => {
 *     await addUser(userData);
 *   };
 *
 *   return <UserForm onSubmit={handleSubmit} loading={isLoading} error={error} />;
 */
export const useAddUser = () => {
  const [state, setState] = useState<HookState<string>>(createInitialState());

  const addUser = useCallback(async (userData: UserData) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.addUser(userData);

    if (result instanceof Error) {
      handleError(setState, result);
    } else {
      handleSuccess(setState, result);
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
 * Campaign Management API Hooks
 */

/**
 * Hook for fetching campaign filter options
 * Returns available filters for campaign data
 */
export const useCampaignFilterOptions = () => {
  const [state, setState] = useState<HookState<CampaignFilterOptions>>(createInitialState());

  const fetchFilterOptions = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchCampaignFilterOptions();

    if (result instanceof Error) {
      handleError(setState, result);
    } else {
      handleSuccess(setState, result);
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

  const resetData = useCallback(() => {
    setState((prev) => ({ ...prev, data: null }));
  }, []);

  return { ...state, uploadCsv, resetData };
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
 * Analytics API Hooks
 */

/**
 * Hook for fetching channel contribution data
 * Returns channel performance metrics for visualization
 */
export const useChannelContribution = () => {
  const [state, setState] = useState<HookState<ChannelContributionData>>(createInitialState());

  const fetchChannelContribution = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchChannelContribution();

    if (result instanceof Error) {
      handleError(setState, result);
    } else {
      handleSuccess(setState, result);
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
 * Prophet Pipeline API Hooks
 */

/**
 * Hook for managing the Prophet prediction pipeline
 * Provides functionality to trigger predictions and check status
 */
export const useProphetPipelineTrigger = () => {
  const [state, setState] = useState<HookState<ProphetPipelineResponse>>(createInitialState());

  const triggerPipeline = useCallback(async (forecastMonths = 4) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.triggerProphetPipeline(forecastMonths);

    if (result instanceof Error) {
      handleError(setState, result);
    } else {
      handleSuccess(setState, result);
    }
  }, []);

  return { ...state, triggerPipeline };
};

/**
 * Hook to check the status of the Prophet prediction pipeline.
 * Returns a function to check the current status and status information.
 */
export const useProphetPipelineStatus = () => {
  const [state, setState] = useState<HookState<ProphetPipelineResponse>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const checkStatus = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.checkProphetPipelineStatus();

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({ data: result, isLoading: false, error: null });
    }
  }, []);

  return { ...state, checkStatus };
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

/**
 * Databases hooks
 */
export const useDatabases = () => {
  const [state, setState] = useState<HookState<string[]>>(createInitialState());

  const fetchDatabases = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.fetchDatabases();

    if (result instanceof Error) {
      handleError(setState, result);
    } else {
      handleSuccess(setState, result.databases);
    }
  }, []);

  return { ...state, fetchDatabases };
};

export const useDeleteDatabase = () => {
  const [state, setState] = useState<HookState<DatabaseDeleteResponse>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const deleteDatabase = useCallback(async (databaseName: string) => {
    setState((prev) => ({ ...prev, isLoading: true }));
    const result = await backendApi.deleteDatabase(databaseName);

    if (result instanceof Error) {
      setState({ data: null, isLoading: false, error: result });
    } else {
      setState({
        data: {
          message: result.message,
          database: result.database,
        },
        isLoading: false,
        error: null,
      });
    }
  }, []);

  return { ...state, deleteDatabase };
};
