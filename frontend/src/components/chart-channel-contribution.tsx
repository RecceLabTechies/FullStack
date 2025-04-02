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

// Define color scheme for different channels
const CHANNEL_COLORS: Record<string, string> = {
  Facebook: '#4267B2',
  Instagram: '#E1306C',
  Google: '#4285F4',
  LinkedIn: '#0077B5',
  TikTok: '#000000',
  Email: '#D44638',
  TV: '#FF0000',
  Search: '#34A853',
  // Add more channels and colors as needed
};

// For any channel not in the above list
const DEFAULT_COLORS = [
  '#8884d8',
  '#83a6ed',
  '#8dd1e1',
  '#82ca9d',
  '#a4de6c',
  '#d0ed57',
  '#ffc658',
  '#ff9e6d',
  '#ffadad',
  '#b0a8b9',
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
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="pt-6 text-red-700">
          <p className="font-medium">Error loading chart data</p>
          <p className="text-sm">{error.message}</p>
        </CardContent>
      </Card>
    );
  }

  if (!data?.channels?.length || !data?.metrics?.length) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-gray-500">
          No data available for channel contribution analysis
        </CardContent>
      </Card>
    );
  }

  // Prepare data for the chart
  const chartData = data.data.map((item) => {
    // Start with the metric name
    const dataPoint: Record<string, string | number> = {
      metric: item.metric,
    };

    // Add values for each channel
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
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="metric"
              label={{ value: 'Metrics', position: 'insideBottom', offset: -5 }}
            />
            <YAxis
              tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              label={{ value: 'Percentage', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip />
            <Legend />
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
