"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Example of transformed data to represent ad spend over time across channels
const transformedData = [
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
  // More data here...
];

export default function SpendingTrendLineChart() {
  return (
    <section className="mt-6">
      <h2 className="mb-4 text-lg font-semibold">
        Spending Trend Over Time Across Channels
      </h2>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={transformedData}
          margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
        >
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />

          {/* Dynamically generate Lines for each channel */}
          {Object.keys(transformedData[0])
            .filter((key) => key !== "date")
            .map((channel, index) => (
              <Line
                key={channel}
                type="monotone"
                dataKey={channel}
                stroke={getColor(index)}
                name={channel}
                dot={false} // Removes dots on data points
              />
            ))}
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}

// Helper function to assign colors dynamically
const getColor = (index) => {
  const colors = [
    "#8884d8",
    "#82ca9d",
    "#ffc658",
    "#d84d4d",
    "#4d79d8",
    "#a832a8",
    "#32a852",
    "#a89d32",
    "#d8a832",
  ];
  return colors[index % colors.length];
};
