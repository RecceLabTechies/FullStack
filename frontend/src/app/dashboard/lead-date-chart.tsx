"use client";

import React, { useEffect, useState } from "react";
import { fetchDbStructure } from "../../api/dbApi";
import { type AdCampaignData } from "@/types/adCampaignTypes";
import {
  LineChart,
  Line,
  XAxis,
  CartesianGrid,
  LabelList,
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
import { TrendingUp } from "lucide-react";

const LeadDateChart = () => {
  const [data, setData] = useState<AdCampaignData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      const result = await fetchDbStructure();
      const campaignData = result?.test_database?.campaign_data_mock ?? [];
      setData(campaignData);
      setIsLoading(false);
      console.log("Fetched data:", campaignData);
    };

    fetchData();
  }, []);

  // Transform data for the line chart
  const transformedData = data.map((row) => ({
    date: row.date,
    leads: row.leads,
  }));

  const chartConfig = {
    leads: {
      label: "Leads",
      color: "hsl(var(--chart-1))",
    },
  } satisfies ChartConfig;

  return (
    <div>
      <h1>Lead Date Chart</h1>
      {isLoading ? (
        <p>Loading data...</p>
      ) : data.length > 0 ? (
        <Card>
          <CardHeader>
            {isLoading ? (
              <>
                <Skeleton className="h-8 w-[200px]" />
                <Skeleton className="h-4 w-[300px]" />
              </>
            ) : (
              <>
                <CardTitle>Lead - Date Chart</CardTitle>
                <CardDescription>January - June 2024</CardDescription>
              </>
            )}
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="h-[200px] w-full">
                <Skeleton className="h-full w-full" />
              </div>
            ) : (
              <ChartContainer config={chartConfig}>
                <LineChart
                  accessibilityLayer
                  width={500}
                  height={300}
                  data={transformedData}
                  margin={{
                    top: 20,
                    left: 12,
                    right: 12,
                  }}
                >
                  <CartesianGrid vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    tickFormatter={(value: string) => value.slice(0, 3)}
                  />
                  <ChartTooltip
                    cursor={false}
                    content={<ChartTooltipContent indicator="line" />}
                  />
                  <Line type="monotone" dataKey="leads" stroke="#8884d8">
                    <LabelList
                      position="top"
                      offset={12}
                      className="fill-foreground"
                      fontSize={12}
                    />
                  </Line>
                </LineChart>
              </ChartContainer>
            )}
          </CardContent>
          <CardFooter>
            {isLoading ? (
              <div className="w-full space-y-2">
                <Skeleton className="h-4 w-[120px]" />
                <Skeleton className="h-4 w-[160px]" />
              </div>
            ) : (
              <div className="flex-col items-start gap-2 text-sm">
                <div className="flex gap-2 font-medium leading-none">
                  Trending up by 5.2% this month{" "}
                  <TrendingUp className="h-4 w-4" />
                </div>
                <div className="leading-none text-muted-foreground">
                  Showing total visitors for the last 6 months
                </div>
              </div>
            )}
          </CardFooter>
        </Card>
      ) : (
        <p>No data available</p>
      )}
    </div>
  );
};

export default LeadDateChart;
