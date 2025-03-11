"use client";

import {
  Area,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const data = [
  {
    month: "Sep 23",
    revenue: 10.2,
    adSpend: 5.2,
    mlRevenue: 10.5,
    mlAdSpend: 5.3,
    projected: false,
  },
  {
    month: "Oct 23",
    revenue: 9.8,
    adSpend: 5.9,
    mlRevenue: 10.8,
    mlAdSpend: 5.5,
    projected: false,
  },
  {
    month: "Nov 23",
    revenue: 17.4,
    adSpend: 6.4,
    mlRevenue: 16.2,
    mlAdSpend: 6.2,
    projected: false,
  },
  {
    month: "Dec 23",
    revenue: 14.8,
    adSpend: 4.9,
    mlRevenue: 15.5,
    mlAdSpend: 5.8,
    projected: false,
  },
  {
    month: "Jan 24",
    revenue: 13.2,
    adSpend: 5.8,
    mlRevenue: 14.8,
    mlAdSpend: 5.9,
    projected: false,
  },
  {
    month: "Feb 24",
    revenue: 12.8,
    adSpend: 5.8,
    mlRevenue: 13.9,
    mlAdSpend: 5.7,
    projected: false,
  },

  {
    month: "Mar 24",
    mlRevenue: 15.3,
    mlAdSpend: 6.1,
    projected: true,
  },
  {
    month: "Apr 24",
    mlRevenue: 16.8,
    mlAdSpend: 6.3,
    projected: true,
  },
  {
    month: "May 24",
    mlRevenue: 18.2,
    mlAdSpend: 6.5,
    projected: true,
  },
  {
    month: "Jun 24",
    mlRevenue: 19.5,
    mlAdSpend: 6.8,
    projected: true,
  },
  {
    month: "Jul 24",
    mlRevenue: 20.8,
    mlAdSpend: 7.0,
    projected: true,
  },
  {
    month: "Aug 24",
    mlRevenue: 22.1,
    mlAdSpend: 7.2,
    projected: true,
  },
];

export default function RevenueChart() {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <defs>
          <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f97316" stopOpacity={0.1} />
            <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="adSpendGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#374151" stopOpacity={0.1} />
            <stop offset="95%" stopColor="#374151" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} tickMargin={10} />
        <YAxis
          domain={[0, 25]}
          tickCount={6}
          label={{
            value: "SGD (Thousands)",
            angle: -90,
            position: "insideLeft",
            style: { textAnchor: "middle" },
          }}
        />
        <Tooltip
          formatter={(value: number) => [`$${value}k`, ""]}
          labelFormatter={(label: string) => `Month: ${label}`}
          contentStyle={{ backgroundColor: "#fff", borderRadius: "6px" }}
        />
        <Legend />

        {/* Actual Revenue */}
        <Line
          type="monotone"
          dataKey="revenue"
          stroke="#ea580c"
          strokeWidth={2}
          dot={{ r: 4, fill: "#ea580c" }}
          activeDot={{ r: 6 }}
          name="Actual Revenue"
        />

        {/* ML Predicted Revenue */}
        <Line
          type="monotone"
          dataKey="mlRevenue"
          stroke="#fb923c"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={{ r: 4, fill: "#fb923c" }}
          activeDot={{ r: 6 }}
          name="ML Predicted Revenue"
        />

        {/* Actual Ad Spend */}
        <Line
          type="monotone"
          dataKey="adSpend"
          stroke="#374151"
          strokeWidth={2}
          dot={{ r: 4, fill: "#374151" }}
          activeDot={{ r: 6 }}
          name="Actual Ad Spend"
        />

        {/* ML Predicted Ad Spend */}
        <Line
          type="monotone"
          dataKey="mlAdSpend"
          stroke="#9ca3af"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={{ r: 4, fill: "#9ca3af" }}
          activeDot={{ r: 6 }}
          name="ML Predicted Ad Spend"
        />

        {/* Gradient Areas */}
        <Area
          type="monotone"
          dataKey="mlRevenue"
          fill="url(#revenueGradient)"
          stroke="transparent"
          fillOpacity={1}
          data={data.filter((d) => d.projected)}
        />
        <Area
          type="monotone"
          dataKey="mlAdSpend"
          fill="url(#adSpendGradient)"
          stroke="transparent"
          fillOpacity={1}
          data={data.filter((d) => d.projected)}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
