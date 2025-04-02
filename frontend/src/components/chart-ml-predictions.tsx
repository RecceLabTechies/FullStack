'use client';

import { useEffect, useMemo, useState } from 'react';

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';

import { useLatestTwelveMonths, useProphetPredictions } from '@/hooks/use-backend-api';

export function MLPredictionsChart() {
  const {
    data: latestTwelveMonthsData,
    isLoading: isLoadingLatestTwelveMonths,
    error: latestTwelveMonthsError,
    fetchLatestTwelveMonths,
  } = useLatestTwelveMonths();

  const {
    data: prophetData,
    isLoading: isLoadingProphet,
    error: prophetError,
    fetchPredictions,
  } = useProphetPredictions();

  // State for prediction months slider
  const [predictionMonths, setPredictionMonths] = useState<number>(0);
  const [selectedMetric, setSelectedMetric] = useState<'revenue' | 'accounts'>('revenue');

  const maxPredictionMonths = useMemo(
    () => (Array.isArray(prophetData) ? prophetData.length : 0),
    [prophetData]
  );

  // Effect to fetch latest twelve months data
  useEffect(() => {
    void fetchLatestTwelveMonths();
    void fetchPredictions(); // Fetch prophet predictions
  }, [fetchLatestTwelveMonths, fetchPredictions]);

  // Effect to reset prediction months when data changes
  useEffect(() => {
    if (maxPredictionMonths > 0 && predictionMonths === 0) {
      setPredictionMonths(maxPredictionMonths);
    }
  }, [maxPredictionMonths, predictionMonths]);

  // Transform and combine latest twelve months data and prophet predictions for the chart
  const combinedChartData = useMemo(() => {
    if (!latestTwelveMonthsData?.items && !prophetData) return [];

    const allData = new Map<
      number,
      {
        month: string;
        revenue?: number;
        ad_spend?: number;
        new_accounts?: number;
        predicted_revenue?: number;
        predicted_ad_spend?: number;
        predicted_new_accounts?: number;
      }
    >();

    // Add actual data
    latestTwelveMonthsData?.items?.forEach((item) => {
      allData.set(item.date, {
        month: new Date(item.date * 1000).toLocaleDateString('default', {
          month: 'short',
          year: '2-digit',
        }),
        revenue: item.revenue,
        ad_spend: item.ad_spend,
        new_accounts: item.new_accounts,
      });
    });

    // Add prophet predictions based on slider value
    if (Array.isArray(prophetData) && predictionMonths > 0) {
      // Sort prophet data by date and take only the number of months specified by the slider
      const sortedProphetData = [...prophetData]
        .sort((a, b) => a.date - b.date)
        .slice(0, predictionMonths);

      sortedProphetData.forEach((item) => {
        const existingData = allData.get(item.date) ?? {
          month: new Date(item.date * 1000).toLocaleDateString('default', {
            month: 'short',
            year: '2-digit',
          }),
        };

        allData.set(item.date, {
          ...existingData,
          predicted_revenue: item.revenue,
          predicted_ad_spend: item.ad_spend,
          predicted_new_accounts: item.new_accounts,
        });
      });
    }

    // Convert map to array and sort by date
    return Array.from(allData.entries())
      .sort(([dateA], [dateB]) => dateA - dateB)
      .map(([_, data]) => data);
  }, [latestTwelveMonthsData, prophetData, predictionMonths]);

  const handleSliderChange = (value: number[]) => {
    setPredictionMonths(value[0] ?? 0);
  };

  const renderChart = () => {
    if (selectedMetric === 'revenue') {
      return (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={combinedChartData}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="hsl(var(--chart-1))"
              activeDot={{ r: 8 }}
              name="Revenue"
            />
            <Line
              type="monotone"
              dataKey="predicted_revenue"
              stroke="hsl(var(--chart-1))"
              strokeDasharray="5 5"
              name="Predicted Revenue"
            />
            <Line type="monotone" dataKey="ad_spend" stroke="hsl(var(--chart-2))" name="Ad Spend" />
            <Line
              type="monotone"
              dataKey="predicted_ad_spend"
              stroke="hsl(var(--chart-2))"
              strokeDasharray="5 5"
              name="Predicted Ad Spend"
            />
          </LineChart>
        </ResponsiveContainer>
      );
    }

    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={combinedChartData}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="new_accounts"
            stroke="hsl(var(--chart-3))"
            activeDot={{ r: 8 }}
            name="New Accounts"
          />
          <Line
            type="monotone"
            dataKey="predicted_new_accounts"
            stroke="hsl(var(--chart-3))"
            strokeDasharray="5 5"
            name="Predicted New Accounts"
          />
        </LineChart>
      </ResponsiveContainer>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>ML Predictions</CardTitle>
            <CardDescription>Monthly comparison of actual and predicted metrics</CardDescription>
          </div>
          <Select
            value={selectedMetric}
            onValueChange={(value: 'revenue' | 'accounts') => setSelectedMetric(value)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select metrics" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="revenue">Revenue & Ad Spend</SelectItem>
              <SelectItem value="accounts">New Accounts</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {(latestTwelveMonthsError ?? prophetError) ? (
          <div className="flex h-[400px] w-full items-center justify-center text-muted-foreground">
            {latestTwelveMonthsError?.message ?? prophetError?.message}
          </div>
        ) : isLoadingLatestTwelveMonths || isLoadingProphet ? (
          <div className="flex h-[400px] w-full items-center justify-center text-muted-foreground">
            Loading...
          </div>
        ) : combinedChartData.length === 0 ? (
          <div className="flex h-[400px] w-full items-center justify-center text-muted-foreground">
            No data available
          </div>
        ) : (
          <>
            <div className="h-[400px] w-full">{renderChart()}</div>
            <div className="mt-6 space-y-2">
              <div className="flex justify-between">
                <Label htmlFor="prediction-months">Prediction Months: {predictionMonths}</Label>
                <span className="text-sm text-muted-foreground">
                  {predictionMonths === 0
                    ? 'No predictions'
                    : `Showing ${predictionMonths} month${predictionMonths === 1 ? '' : 's'}`}
                </span>
              </div>
              <Slider
                id="prediction-months"
                min={0}
                max={maxPredictionMonths}
                step={1}
                value={[predictionMonths]}
                onValueChange={handleSliderChange}
                className="w-full"
                disabled={isLoadingProphet || maxPredictionMonths === 0}
              />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
