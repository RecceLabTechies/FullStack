import { useState } from "react";
import {
  type AnalysisResponse,
  analyzeData,
  isChartResponse,
  isDescriptionResponse,
  isErrorResponse,
  isReportResponse,
} from "@/api/llmApi";

interface LlmAnalysisState {
  data: AnalysisResponse | null;
  loading: boolean;
  error: Error | null;
  isChart: boolean;
  isDescription: boolean;
  isReport: boolean;
  isError: boolean;
}

export const useLlmAnalysis = () => {
  const [state, setState] = useState<LlmAnalysisState>({
    data: null,
    loading: false,
    error: null,
    isChart: false,
    isDescription: false,
    isReport: false,
    isError: false,
  });

  const analyze = async (query: string) => {
    setState({
      ...state,
      loading: true,
      error: null,
      isChart: false,
      isDescription: false,
      isReport: false,
      isError: false,
    });

    try {
      const data = await analyzeData(query);

      setState({
        data,
        loading: false,
        error: null,
        isChart: isChartResponse(data),
        isDescription: isDescriptionResponse(data),
        isReport: isReportResponse(data),
        isError: isErrorResponse(data),
      });

      return data;
    } catch (error) {
      setState({
        ...state,
        data: null,
        loading: false,
        error: error as Error,
        isError: true,
      });
      return null;
    }
  };

  return {
    ...state,
    analyze,
  };
};
