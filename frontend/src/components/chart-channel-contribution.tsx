import { useEffect } from 'react';

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

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

import { useChannelContribution } from '@/hooks/use-backend-api';

// Define color scheme for different channels using CSS variables
const CHANNEL_COLORS: Record<string, string> = {
  Facebook: 'hsl(var(--chart-1))',
  Instagram: 'hsl(var(--chart-2))',
  Google: 'hsl(var(--chart-3))',
  LinkedIn: 'hsl(var(--chart-4))',
  TikTok: 'hsl(var(--chart-5))',
  Email: 'hsl(var(--chart-6))',
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

  useEffect(() => {
    void fetchChannelContribution();
  }, [fetchChannelContribution]);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
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
        <CardContent className="flex justify-center items-center h-[30rem] text-destructive">
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
        <CardContent className="flex justify-center items-center h-[30rem] text-muted-foreground">
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
      <CardHeader>
        <CardTitle>Channel Contribution by Metric</CardTitle>
        {data.time_range?.from_ && data.time_range?.to && (
          <CardDescription>
            Data from {data.time_range.from_} to {data.time_range.to}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="h-[30rem]">
        <ResponsiveContainer width="100%" height="100%">
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
