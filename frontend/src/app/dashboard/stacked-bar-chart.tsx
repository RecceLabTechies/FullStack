"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Transform data to be grouped by percentage categories instead of channels
const transformedData = [
  {
    category: "Spending",
    Influencer: 10,
    "Sponsored search ads": 20,
    "TikTok ads": 20,
    "Instagram Ads": 4,
    Email: 2,
    LinkedIn: 4,
    "Radio ads": 3,
    "TV ads": 3,
    "Google banner ads": 34,
  },
  {
    category: "Views",
    Influencer: 10,
    "Sponsored search ads": 15,
    "TikTok ads": 11,
    "Instagram Ads": 10,
    Email: 4,
    LinkedIn: 15,
    "Radio ads": 10,
    "TV ads": 15,
    "Google banner ads": 10,
  },
  {
    category: "Leads",
    Influencer: 11,
    "Sponsored search ads": 11,
    "TikTok ads": 25,
    "Instagram Ads": 10,
    Email: 13,
    LinkedIn: 6,
    "Radio ads": 10,
    "TV ads": 4,
    "Google banner ads": 10,
  },
  {
    category: "New Accounts",
    Influencer: 5,
    "Sponsored search ads": 10,
    "TikTok ads": 20,
    "Instagram Ads": 30,
    Email: 18,
    LinkedIn: 5,
    "Radio ads": 5,
    "TV ads": 5,
    "Google banner ads": 2,
  },
  {
    category: "Revenue",
    Influencer: 15,
    "Sponsored search ads": 25,
    "TikTok ads": 10,
    "Instagram Ads": 10,
    Email: 5,
    LinkedIn: 10,
    "Radio ads": 10,
    "TV ads": 10,
    "Google banner ads": 5,
  },
];

export default function StackedBarChart() {
  return (
    <section className="mt-6">
      <h2 className="mb-4 text-lg font-semibold">
        Stacked Bar Chart: Percentage Contribution by Category
      </h2>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={transformedData}
          margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
        >
          <XAxis dataKey="category" />
          <YAxis tickFormatter={(tick) => `${tick}%`} />
          <Tooltip />
          <Legend />

          {/* Dynamically generate Bars for each channel */}
          {Object.keys(transformedData[0])
            .filter((key) => key !== "category")
            .map((channel, index) => (
              <Bar
                key={channel}
                dataKey={channel}
                stackId="a"
                fill={getColor(index)}
                name={channel}
              />
            ))}
        </BarChart>
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
