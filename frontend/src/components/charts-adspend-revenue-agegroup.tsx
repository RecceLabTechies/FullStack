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

import { useMonthlyAgeData } from '@/hooks/use-backend-api';

interface DataPoint {
  date: string;
  revenue: number;
  ad_spend: number;
  avg_revenue: number;
  avg_ad_spend: number;
}

// Color palette for different age groups
const AGE_GROUP_COLORS = {
  '18-24': { revenue: 'hsl(var(--chart-1))', ad_spend: 'hsl(var(--chart-2))' },
  '25-34': { revenue: 'hsl(var(--chart-3))', ad_spend: 'hsl(var(--chart-4))' },
  '35-44': { revenue: 'hsl(var(--chart-5))', ad_spend: 'hsl(var(--chart-6))' },
  '45-54': { revenue: 'hsl(var(--chart-7))', ad_spend: 'hsl(var(--chart-8))' },
  '55-64': { revenue: 'hsl(var(--chart-9))', ad_spend: 'hsl(var(--chart-10))' },
  '65+': { revenue: 'hsl(var(--chart-11))', ad_spend: 'hsl(var(--chart-12))' },
};

const AgeGroupPerformanceCharts = () => {
  const { data, isLoading, error, fetchMonthlyAgeData } = useMonthlyAgeData();

  useEffect(() => {
    void fetchMonthlyAgeData();
  }, [fetchMonthlyAgeData]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Age Group Performance Trends</CardTitle>
          <CardDescription>
            Monthly comparison of revenue and ad spend across different age groups
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
          <CardTitle>Age Group Performance Trends</CardTitle>
          <CardDescription>
            Monthly comparison of revenue and ad spend across different age groups
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

  if (!data?.age_groups?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Age Group Performance Trends</CardTitle>
          <CardDescription>
            Monthly comparison of revenue and ad spend across different age groups
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

  // Prepare the individual chart data for each age group
  const ageGroupCharts = data.age_groups.map((ageGroup) => {
    // Calculate averages first
    const revenues = data.revenue?.[ageGroup] ?? [];
    const adSpends = data.ad_spend?.[ageGroup] ?? [];
    const avgRevenue = revenues.reduce((sum, val) => sum + (val ?? 0), 0) / revenues.length;
    const avgAdSpend = adSpends.reduce((sum, val) => sum + (val ?? 0), 0) / adSpends.length;

    // Transform data for this specific age group
    const chartData: DataPoint[] = data.months.map((month, index) => {
      return {
        date: format(new Date(month * 1000), 'MMM yyyy'),
        revenue: data.revenue?.[ageGroup]?.[index] ?? 0,
        ad_spend: data.ad_spend?.[ageGroup]?.[index] ?? 0,
        avg_revenue: avgRevenue,
        avg_ad_spend: avgAdSpend,
      };
    });

    // Get colors for this age group
    const colors = AGE_GROUP_COLORS[ageGroup as keyof typeof AGE_GROUP_COLORS] || {
      revenue: 'hsl(var(--chart-1))',
      ad_spend: 'hsl(var(--chart-2))',
    };

    return (
      <Card key={ageGroup}>
        <CardHeader>
          <CardTitle>Age Group: {ageGroup}</CardTitle>
          <CardDescription>
            Monthly comparison of revenue generated versus advertising expenditure for age{' '}
            {ageGroup}
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
              <Tooltip
                formatter={(value: number) => [
                  `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
                  '',
                ]}
              />
              <Legend />
              <Line
                strokeWidth={2}
                type="monotone"
                dataKey="revenue"
                name="Revenue"
                stroke={colors.revenue}
                dot={{ r: 4 }}
                activeDot={{ r: 8 }}
              />
              <Line
                strokeWidth={2}
                type="monotone"
                dataKey="ad_spend"
                name="Ad Spend"
                stroke={colors.ad_spend}
                dot={{ r: 4 }}
              />
              <Line
                strokeWidth={2}
                type="monotone"
                dataKey="avg_revenue"
                name="Avg Revenue"
                stroke={colors.revenue}
                strokeDasharray="5 5"
                dot={false}
              />
              <Line
                strokeWidth={2}
                type="monotone"
                dataKey="avg_ad_spend"
                name="Avg Ad Spend"
                stroke={colors.ad_spend}
                strokeDasharray="5 5"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  });

  return <div className="grid grid-cols-3 gap-2">{ageGroupCharts}</div>;
};

export default AgeGroupPerformanceCharts;
