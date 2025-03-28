import axios from "axios";

// Define report results type
export interface ReportResults {
  results: Array<{
    description?: string;
    chart?: string | Record<string, unknown>;
    [key: string]: string | Record<string, unknown> | undefined;
  }>;
}

// Output types from the backend API
export interface BackendOutput {
  error?: string;
  chart?: string;
  description?: string;
  report?: {
    report: ReportResults;
  };
}

// Response from the backend API
export interface AnalysisResponse {
  output: BackendOutput;
  original_query: string;
}

// Type guards
export function isChartResponse(response: AnalysisResponse): boolean {
  return (
    response.output && "chart" in response.output && !!response.output.chart
  );
}

export function isDescriptionResponse(response: AnalysisResponse): boolean {
  return (
    response.output &&
    "description" in response.output &&
    !!response.output.description
  );
}

export function isReportResponse(response: AnalysisResponse): boolean {
  return (
    response.output && "report" in response.output && !!response.output.report
  );
}

export function isErrorResponse(response: AnalysisResponse): boolean {
  return (
    response.output && "error" in response.output && !!response.output.error
  );
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
