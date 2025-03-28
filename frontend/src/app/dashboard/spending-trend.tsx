"use client";

import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { format, parseISO } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

type SpendingDataPoint = {
  date: string;
  [channel: string]: string | number;
};

const sampleData: SpendingDataPoint[] = [
  {
    date: "2022-01-02",
    Influencer: 233,
    "Sponsored search ads": 200,
    "TikTok ads": 150,
    Instagram: 100,
  },
  {
    date: "2022-01-03",
    Influencer: 250,
    "Sponsored search ads": 220,
    "TikTok ads": 160,
    Instagram: 110,
  },
  {
    date: "2022-01-04",
    Influencer: 300,
    "Sponsored search ads": 250,
    "TikTok ads": 170,
    Instagram: 120,
  },
];

const CHANNEL_COLORS: Record<string, string> = {
  Influencer: "#8884d8",
  "Sponsored search ads": "#82ca9d",
  "TikTok ads": "#ffc658",
  Instagram: "#ff8042",
};

export default function SpendingTrendLineChart() {
  const [data, setData] = useState<SpendingDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = () => {
      setIsLoading(true);
      setTimeout(() => {
        setData(sampleData);
        setIsLoading(false);
      }, 500);
    };

    fetchData();
  }, []);

  const formatDate = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), "MMM d");
    } catch {
      return dateStr;
    }
  };

  const channels =
    data.length > 0
      ? Object.keys(data[0] ?? {}).filter((key) => key !== "date")
      : [];

  if (isLoading) {
    return (
      <Card className="flex h-64 items-center justify-center">
        <CardContent>
          <Loader2 className="animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Spending Trend Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              opacity={0.3}
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fill: "#6b7280" }}
            />
            <YAxis
              tickFormatter={(value) => `$${value}`}
              tick={{ fill: "#6b7280" }}
            />
            <Tooltip
              formatter={(value: number | string) => [`$${value}`, ``]}
              labelFormatter={(label: string) => formatDate(label)}
            />
            <Legend />

            {channels.map((channel, index) => (
              <Line
                key={channel}
                type="monotone"
                dataKey={channel}
                name={channel}
                stroke={
                  CHANNEL_COLORS[channel] ?? `hsl(${index * 30}, 70%, 50%)`
                }
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
