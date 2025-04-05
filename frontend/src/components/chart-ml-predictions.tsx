'use client';

import { useEffect, useMemo, useState } from 'react';

import { useDatabaseOperations } from '@/context/database-operations-context';
import { useProphetPredictionsContext } from '@/context/prophet-predictions-context';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { useLatestTwelveMonths } from '@/hooks/use-backend-api';

export function MLPredictionsChart() {
  const {
    data: latestTwelveMonthsData,
    isLoading: isLoadingLatestTwelveMonths,
    error: latestTwelveMonthsError,
    fetchLatestTwelveMonths,
  } = useLatestTwelveMonths();

  const { lastUpdated: dbLastUpdated } = useDatabaseOperations();

  const {
    data: prophetData,
    isLoading: isLoadingProphet,
    error: prophetError,
    lastUpdated: predictionLastUpdated,
  } = useProphetPredictionsContext();

  const [selectedMetric, setSelectedMetric] = useState<'revenue' | 'accounts'>('revenue');

  // Effect to fetch latest twelve months data when database or predictions update
  useEffect(() => {
    console.log('MLPredictionsChart: Fetching latest data due to update', {
      dbLastUpdated,
      predictionLastUpdated,
    });
    void fetchLatestTwelveMonths();
  }, [fetchLatestTwelveMonths, dbLastUpdated, predictionLastUpdated]);

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

    // Add all prophet predictions
    if (Array.isArray(prophetData) && prophetData.length > 0) {
      // Sort prophet data by date
      const sortedProphetData = [...prophetData].sort((a, b) => a.date - b.date);

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
  }, [latestTwelveMonthsData, prophetData]);

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
              strokeWidth={3}
              name="Revenue"
            />
            <Line
              type="monotone"
              dataKey="predicted_revenue"
              stroke="hsl(var(--chart-1))"
              strokeDasharray="5 5"
              strokeWidth={5}
              name="Predicted Revenue"
            />
            <Line
              type="monotone"
              dataKey="ad_spend"
              stroke="hsl(var(--chart-2))"
              name="Ad Spend"
              strokeWidth={3}
            />
            <Line
              type="monotone"
              dataKey="predicted_ad_spend"
              stroke="hsl(var(--chart-2))"
              strokeDasharray="5 5"
              strokeWidth={5}
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
            strokeWidth={3}
            name="New Accounts"
          />
          <Line
            type="monotone"
            dataKey="predicted_new_accounts"
            stroke="hsl(var(--chart-3))"
            strokeWidth={5}
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
          <div className="h-[400px] w-full">{renderChart()}</div>
        )}
      </CardContent>
    </Card>
  );
}
