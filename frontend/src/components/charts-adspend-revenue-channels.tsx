import { useEffect } from 'react';

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

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

import { useMonthlyChannelData } from '@/hooks/use-backend-api';

interface DataPoint {
  date: string;
  revenue: number;
  ad_spend: number;
  avg_revenue: number;
  avg_ad_spend: number;
}

const ChannelPerformanceCharts = () => {
  const { data, isLoading, error, fetchMonthlyChannelData } = useMonthlyChannelData();

  useEffect(() => {
    void fetchMonthlyChannelData();
  }, [fetchMonthlyChannelData]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Channel Performance Trends</CardTitle>
          <CardDescription>
            Monthly comparison of revenue and ad spend across different channels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex h-[400px] w-full items-center justify-center text-muted-foreground">
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
          <div className="flex h-[400px] w-full items-center justify-center text-muted-foreground">
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
          <div className="flex h-[400px] w-full items-center justify-center text-muted-foreground">
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
          <CardTitle>{channel} Performance</CardTitle>
          <CardDescription>
            Monthly comparison of revenue generated versus advertising expenditure for {channel}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
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
              <Tooltip />
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

  return <div className="grid grid-cols-3 gap-2">{channelCharts}</div>;
};

export default ChannelPerformanceCharts;
