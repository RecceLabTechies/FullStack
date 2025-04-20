import { useEffect, useState } from 'react';
import { type DateRange } from 'react-day-picker';

import { useDatabaseOperations } from '@/context/database-operations-context';
import { Info } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { DatePickerWithRange } from '@/components/date-range-picker';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';

import { useCampaignDateRange, useChannelContribution } from '@/hooks/use-backend-api';

// Define color scheme for different channels using CSS variables
const CHANNEL_COLORS: Record<string, string> = {
  Facebook: 'hsl(var(--chart-1))',
  Email: 'hsl(var(--chart-2))',
  Google: 'hsl(var(--chart-3))',
  LinkedIn: 'hsl(var(--chart-4))',
  TikTok: 'hsl(var(--chart-5))',
  Instagram: 'hsl(var(--chart-6))',
  TV: 'hsl(var(--chart-7))',
  Search: 'hsl(var(--chart-8))',
};

// For any channel not in the above list, use the remaining chart colors
const DEFAULT_COLORS = [
  'hsl(var(--chart-9))',
  'hsl(var(--chart-10))',
  'hsl(var(--chart-11))',
  'hsl(var(--chart-12))',
  'hsl(var(--chart-13))',
  'hsl(var(--chart-14))',
  'hsl(var(--chart-15))',
  'hsl(var(--chart-16))',
  'hsl(var(--chart-17))',
  'hsl(var(--chart-18))',
];

/**
 * A component that displays a stacked bar chart showing the percentage contribution
 * of each channel across different metrics (spending, views, leads, etc.)
 */
export default function ChannelContributionChart() {
  const { data, isLoading, error, fetchChannelContribution } = useChannelContribution();
  const {
    data: dateRangeData,
    isLoading: isDateRangeLoading,
    fetchDateRange,
  } = useCampaignDateRange();
  const { lastUpdated } = useDatabaseOperations();
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);

  // Fetch available date range on mount
  useEffect(() => {
    void fetchDateRange();
  }, [fetchDateRange, lastUpdated]);

  // Fetch data with date range filter
  useEffect(() => {
    const minDate = dateRange?.from ? Math.floor(dateRange.from.getTime() / 1000) : undefined;
    const maxDate = dateRange?.to ? Math.floor(dateRange.to.getTime() / 1000) : undefined;
    void fetchChannelContribution(minDate, maxDate);
  }, [fetchChannelContribution, dateRange, lastUpdated]);

  // Convert Unix timestamps to Date objects for the date picker
  const minDate = dateRangeData?.min_date ? new Date(dateRangeData.min_date * 1000) : undefined;
  const maxDate = dateRangeData?.max_date ? new Date(dateRangeData.max_date * 1000) : undefined;

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex justify-center items-center h-64">
          <div
            className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"
            aria-label="Loading chart data"
            role="status"
          ></div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Channel Contribution by Metric</CardTitle>
          <CardDescription>Error loading data</CardDescription>
        </CardHeader>
        <CardContent
          className="flex justify-center items-center h-[30rem] text-destructive"
          role="alert"
        >
          <p>{error.message}</p>
        </CardContent>
      </Card>
    );
  }

  if (!data?.channels?.length || !data?.metrics?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Channel Contribution by Metric</CardTitle>
          <CardDescription>
            {data?.time_range?.from_ && data?.time_range?.to
              ? `Data from ${data.time_range.from_} to ${data.time_range.to}`
              : 'No data available'}
          </CardDescription>
        </CardHeader>
        <CardContent
          className="flex justify-center items-center h-[30rem] text-muted-foreground"
          aria-label="No channel contribution data available"
        >
          No data available for channel contribution analysis
        </CardContent>
      </Card>
    );
  }

  // Prepare data for the chart
  const chartData = data.data.map((item) => {
    const dataPoint: Record<string, string | number> = {
      metric: item.metric,
    };

    Object.entries(item.values).forEach(([channel, value]) => {
      dataPoint[channel] = value;
    });

    return dataPoint;
  });

  return (
    <Card>
      <div className="flex items-center justify-between pr-6">
        <CardHeader>
          <CardTitle id="channel-contribution-title">Channel Contribution by Metric</CardTitle>
          <DatePickerWithRange
            onRangeChange={setDateRange}
            initialDateRange={dateRange}
            minDate={minDate}
            maxDate={maxDate}
            className="w-[300px]"
          />
        </CardHeader>
        <HoverCard>
          <HoverCardTrigger asChild>
            <Info
              className="h-4 w-4 text-muted-foreground cursor-help"
              aria-label="About channel performance distribution"
            />
          </HoverCardTrigger>
          <HoverCardContent className="w-[320px]">
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Channel Performance Distribution</h4>
              <p className="text-sm text-muted-foreground">
                This stacked bar chart shows how different advertising channels contribute to each
                metric as a percentage. Each bar represents 100% of a metric, split by channel
                contribution.
              </p>
              <p className="text-sm text-muted-foreground">
                <strong>Calculation method:</strong> For each metric, the raw values for all
                channels are summed, then each channel&apos;s value is divided by this total to get
                its percentage contribution (0-100%).
              </p>
              <p className="text-sm text-muted-foreground">
                <strong>Interpretation:</strong> Taller segments indicate channels with higher
                contribution to that metric. This normalization allows for comparing channel
                distribution across metrics with different value ranges.
              </p>
              <p className="text-sm text-muted-foreground">
                Use this visualization to identify your top-performing channels for each metric and
                detect imbalances in your marketing mix.
              </p>
            </div>
          </HoverCardContent>
        </HoverCard>
      </div>

      <div className="px-6 pb-2"></div>

      <CardContent className="h-[30rem]">
        <ResponsiveContainer
          width="100%"
          height="100%"
          aria-labelledby="channel-contribution-title"
        >
          <BarChart data={chartData} margin={{ right: 30, left: 20 }} stackOffset="expand">
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="metric"
              label={{ value: 'Metrics', position: 'insideBottom', offset: -5 }}
              className="text-muted-foreground"
            />
            <YAxis
              tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              label={{ value: 'Percentage', angle: -90, position: 'insideLeft' }}
              className="text-muted-foreground"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                borderColor: 'hsl(var(--border))',
                color: 'hsl(var(--foreground))',
              }}
            />
            <Legend className="text-muted-foreground" />
            {data.channels.map((channel, index) => (
              <Bar
                key={channel}
                dataKey={channel}
                stackId="a"
                fill={CHANNEL_COLORS[channel] ?? DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
                name={channel}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
