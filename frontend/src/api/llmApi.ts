import axios from "axios";

// Define report results type
export interface ReportResults {
  results: Array<string>;
}

// Response from the backend API
export interface AnalysisResponse {
  output: string | ReportResults | null;
  original_query: string;
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

// Helper function to check if the response is a chart image URL (new format)
export const isChartImageResponse = (response: AnalysisResponse): boolean => {
  return (
    response.output !== null &&
    typeof response.output === "string" &&
    (response.output.startsWith("http://") ||
      response.output.startsWith("https://")) &&
    (response.output.includes(".png") ||
      response.output.includes(".jpg") ||
      response.output.includes(".jpeg"))
  );
};

// Helper function to check if the response is a report
export const isReportResponse = (response: AnalysisResponse): boolean => {
  return (
    response.output !== null &&
    typeof response.output === "object" &&
    "results" in response.output
  );
};
