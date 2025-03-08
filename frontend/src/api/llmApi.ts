import axios from "axios";

export interface AnalysisResponse {
  success: boolean;
  result?: {
    selected_json: string;
    original_query: string;
    query_type: "chart" | "description" | "report";
    output: string;
    data_preview?: Record<string, any>;
    data_shape?: {
      rows: number;
      columns: number;
    };
    columns?: string[];
  };
  error?: string;
}

const LLM_API_BASE_URL = "http://localhost:5000";

export const analyzeData = async (query: string): Promise<AnalysisResponse> => {
  try {
    const response = await axios.post(`${LLM_API_BASE_URL}/api/analyze`, {
      query,
    });
    return response.data as AnalysisResponse;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data) {
      return error.response.data as AnalysisResponse;
    }
    return {
      success: false,
      error: "Failed to connect to analysis service",
    };
  }
};

// Helper function to check if the response contains a chart
export const isChartResponse = (
  result: AnalysisResponse["result"],
): boolean => {
  return result?.query_type === "chart";
};

// Helper function to check if the response contains a report
export const isReportResponse = (
  result: AnalysisResponse["result"],
): boolean => {
  return result?.query_type === "report";
};
