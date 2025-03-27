import axios from "axios";

// Define the chart data types based on backend types
export interface AxisConfig {
  dataKey: string;
  label: string;
  type: string;
}

export interface ChartDataType {
  data: Record<string, unknown>[];
  type: string;
  xAxis: AxisConfig;
  yAxis: AxisConfig;
}

// Define report results type
export interface ReportResults {
  results: Array<string | ChartDataType>;
}

// Response from the backend API
export interface AnalysisResponse {
  output: string | ChartDataType | ReportResults | null;
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

// Helper function to check if the response is a chart
export const isChartResponse = (response: AnalysisResponse): boolean => {
  return (
    response.output !== null &&
    typeof response.output === "object" &&
    "type" in response.output &&
    "data" in response.output &&
    "xAxis" in response.output &&
    "yAxis" in response.output
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
