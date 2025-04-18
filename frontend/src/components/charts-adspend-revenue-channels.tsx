import { useEffect, useState } from 'react';
import { DateRange } from 'react-day-picker';

import { useDatabaseOperations } from '@/context/database-operations-context';
import { format } from 'date-fns';
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

import { DatePickerWithRange } from '@/components/date-range-picker';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

import { useCampaignDateRange, useMonthlyChannelData } from '@/hooks/use-backend-api';

interface DataPoint {
  date: string;
  revenue: number;
  ad_spend: number;
  avg_revenue: number;
  avg_ad_spend: number;
}

const ChannelPerformanceCharts = () => {
  const { data, isLoading, error, fetchMonthlyChannelData } = useMonthlyChannelData();
  const {
    data: dateRangeData,
    isLoading: isDateRangeLoading,
    fetchDateRange,
  } = useCampaignDateRange();
  const { lastUpdated } = useDatabaseOperations();
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);

  // Fetch date range data on mount
  useEffect(() => {
    void fetchDateRange();
  }, [fetchDateRange, lastUpdated]);

  // Fetch data with date range filter
  useEffect(() => {
    const minDate = dateRange?.from ? Math.floor(dateRange.from.getTime() / 1000) : undefined;
    const maxDate = dateRange?.to ? Math.floor(dateRange.to.getTime() / 1000) : undefined;
    void fetchMonthlyChannelData(minDate, maxDate);
  }, [fetchMonthlyChannelData, dateRange, lastUpdated]);

  // Date range change handler
  const handleDateRangeChange = (range: DateRange | undefined) => {
    setDateRange(range);
  };

  // Convert timestamps to Date objects for min/max date constraints
  const minDate = dateRangeData?.min_date ? new Date(dateRangeData.min_date * 1000) : undefined;
  const maxDate = dateRangeData?.max_date ? new Date(dateRangeData.max_date * 1000) : undefined;

  if (isLoading || isDateRangeLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Channel Performance Trends</CardTitle>
          <CardDescription>
            Monthly comparison of revenue and ad spend across different channels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="flex h-[400px] w-full items-center justify-center text-muted-foreground"
            role="status"
            aria-live="polite"
          >
            Loading...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Channel Performance Trends</CardTitle>
          <CardDescription>
            Monthly comparison of revenue and ad spend across different channels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="flex h-[400px] w-full items-center justify-center text-muted-foreground"
            role="alert"
          >
            {error.message}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data?.channels?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Channel Performance Trends</CardTitle>
          <CardDescription>
            Monthly comparison of revenue and ad spend across different channels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="flex h-[400px] w-full items-center justify-center text-muted-foreground"
            aria-label="No channel data available"
          >
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare the individual chart data for each channel
  const channelCharts = data.channels.map((channel) => {
    // Calculate averages first
    const revenues = data.revenue?.[channel] ?? [];
    const adSpends = data.ad_spend?.[channel] ?? [];
    const avgRevenue = revenues.reduce((sum, val) => sum + (val ?? 0), 0) / revenues.length;
    const avgAdSpend = adSpends.reduce((sum, val) => sum + (val ?? 0), 0) / adSpends.length;

    // Transform data for this specific channel
    const chartData: DataPoint[] = data.months.map((month, index) => {
      return {
        date: format(new Date(month * 1000), 'MMM yyyy'),
        revenue: data.revenue?.[channel]?.[index] ?? 0,
        ad_spend: data.ad_spend?.[channel]?.[index] ?? 0,
        avg_revenue: avgRevenue,
        avg_ad_spend: avgAdSpend,
      };
    });

    return (
      <Card key={channel}>
        <CardHeader>
          <CardTitle id={`channel-${channel.replace(/\s+/g, '-').toLowerCase()}-title`}>
            {channel} Performance
          </CardTitle>
          <CardDescription>
            Monthly comparison of revenue generated versus advertising expenditure for {channel}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer
            width="100%"
            height={300}
            aria-labelledby={`channel-${channel.replace(/\s+/g, '-').toLowerCase()}-title`}
          >
            <LineChart
              data={chartData}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip
                formatter={(value: number | string) =>
                  typeof value === 'number' ? value.toFixed(3) : value
                }
              />
              <Legend />
              <Line
                strokeWidth={2}
                type="monotone"
                dataKey="revenue"
                name="Revenue"
                stroke="hsl(var(--chart-1))"
                dot={{ r: 4 }}
                activeDot={{ r: 8 }}
              />
              <Line
                strokeWidth={2}
                type="monotone"
                dataKey="ad_spend"
                name="Ad Spend"
                stroke="hsl(var(--chart-2))"
                dot={{ r: 4 }}
              />
              <Line
                strokeWidth={2}
                type="monotone"
                dataKey="avg_revenue"
                name="Avg Revenue"
                stroke="hsl(var(--chart-1))"
                strokeDasharray="5 5"
                dot={false}
              />
              <Line
                strokeWidth={2}
                type="monotone"
                dataKey="avg_ad_spend"
                name="Avg Ad Spend"
                stroke="hsl(var(--chart-2))"
                strokeDasharray="5 5"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  });

  return (
    <div className="space-y-2" aria-label="Channel performance charts">
      <Card>
        <CardHeader>
          <CardTitle>Filter Channel Data</CardTitle>
          <CardDescription>Select a date range to filter performance data</CardDescription>
        </CardHeader>
        <CardContent>
          <DatePickerWithRange
            onRangeChange={handleDateRangeChange}
            initialDateRange={dateRange}
            minDate={minDate}
            maxDate={maxDate}
          />
        </CardContent>
      </Card>
      <div className="grid grid-cols-3 gap-2">{channelCharts}</div>
    </div>
  );
};

export default ChannelPerformanceCharts;
