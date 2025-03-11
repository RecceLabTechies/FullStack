import axios from "axios";

export interface AnalysisResponse {
  selected_json: string;
  original_query: string;
  query_type: "chart" | "description" | "report";
  output: string | Record<string, unknown> | null;
  error?: string;
}

const LLM_API_BASE_URL = "http://localhost:5152";

export const analyzeData = async (query: string): Promise<AnalysisResponse> => {
  try {
    const response = await axios.post(`${LLM_API_BASE_URL}/api/query`, {
      query,
    });
    return response.data as AnalysisResponse;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data) {
      return error.response.data as AnalysisResponse;
    }
    throw new Error("Failed to connect to analysis service");
  }
};

export const checkHealth = async (): Promise<{ status: string }> => {
  try {
    const response = await axios.get<{ status: string }>(
      `${LLM_API_BASE_URL}/api/health`,
    );
    return response.data;
  } catch (error: unknown) {
    throw new Error("Health check failed");
  }
};

// Helper function to check if the response contains a chart
export const isChartResponse = (response: AnalysisResponse): boolean => {
  return response.query_type === "chart";
};

// Helper function to check if the response contains a report
export const isReportResponse = (response: AnalysisResponse): boolean => {
  return response.query_type === "report";
};
