"use client";

import React, { useEffect, useState } from "react";
import { fetchRevenueDateChartData, RevenueDateChartData } from "../../api/dbApi";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
} from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

// Loading state component
const ChartLoadingState = () => (
  <Card>
    <CardHeader>
      <Skeleton className="h-8 w-[200px]" />
      <Skeleton className="h-4 w-[300px]" />
    </CardHeader>
    <CardContent>
      <div className="h-[300px] w-full">
        <Skeleton className="h-full w-full" />
      </div>
    </CardContent>
    <CardFooter>
      <div className="w-full space-y-2">
        <Skeleton className="h-4 w-[120px]" />
        <Skeleton className="h-4 w-[160px]" />
      </div>
    </CardFooter>
  </Card>
);

const RevenueChart = () => {
  const [data, setData] = useState<RevenueDateChartData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const result = await fetchRevenueDateChartData();
        if (result) {
          setData(result);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch chart data",
        );
        console.error("Error fetching chart data:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Transform data for the line chart
  const transformedData = data.map((row) => ({
    date: row.date,
    revenue: row.revenue,
  }));

  const chartConfig: ChartConfig = {
    revenue: {
      label: "Revenue",
      color: "hsl(var(--chart-1))",
    },
  };

  // Calculate trend percentage
  const calculateTrend = () => {
    if (data.length < 2) return null;

    const lastEntry = data[data.length - 1];
    const previousEntry = data[data.length - 2];

    if (!lastEntry?.revenue || !previousEntry?.revenue) return null;

    const trend =
      ((lastEntry.revenue - previousEntry.revenue) / previousEntry.revenue) * 100;
    return trend.toFixed(1);
  };

  if (isLoading) {
    return <ChartLoadingState />;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (data.length === 0) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>No data available for the chart</AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl sm:text-2xl">Revenue Tracking</CardTitle>
        <CardDescription className="text-sm sm:text-base">
          January - June 2024
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={transformedData}
              margin={{
                top: 20,
                left: 24,
                right: 24,
                bottom: 20,
              }}
              role="img"
              aria-label="Revenue trends over time"
            >
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={(value: string): string => {
                  try {
                    const date = new Date(value);
                    return date.toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    });
                  } catch {
                    return value;
                  }
                }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={(value) => `$${value}`}
                className="text-xs sm:text-sm"
              />
              <ChartTooltip
                cursor={false}
                content={<ChartTooltipContent indicator="line" />}
              />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
                dot={{
                  strokeWidth: 2,
                  r: 4,
                  className: "cursor-pointer transition-all hover:r-6",
                }}
                activeDot={{
                  r: 6,
                  strokeWidth: 3,
                }}
              >
                <LabelList
                  position="top"
                  offset={12}
                  className="fill-foreground text-xs sm:text-sm"
                  fontSize={12}
                  formatter={(value: number) => `$${value}`}
                />
              </Line>
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
      <CardFooter>
        <div className="flex-col items-start gap-2 text-sm sm:text-base">
          {calculateTrend() && (
            <div className="flex items-center gap-2 font-medium leading-none">
              Trending {Number(calculateTrend()) >= 0 ? "up" : "down"} by{" "}
              {Math.abs(Number(calculateTrend()))}% this month
              <TrendingUp
                className={`h-4 w-4 ${Number(calculateTrend()) >= 0 ? "text-green-500" : "text-red-500"}`}
              />
            </div>
          )}
          <div className="mt-1 leading-none text-muted-foreground">
            Showing total revenue for the last 6 months
          </div>
        </div>
      </CardFooter>
    </Card>
  );
};

export default RevenueChart;
