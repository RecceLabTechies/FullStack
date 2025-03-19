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

// will update with API
const rawData = [
  {
    time: "Apr-15",
    channel: "Influencer",
    percentage_spending: 10,
    percentage_views: 10,
    percentage_leads: 0,
    percentage_accounts: 5,
    percentage_revenue: 30,
  },
  {
    time: "Apr-15",
    channel: "Sponsored search ads",
    percentage_spending: 20,
    percentage_views: 15,
    percentage_leads: 0,
    percentage_accounts: 10,
    percentage_revenue: 40,
  },
  {
    time: "Apr-15",
    channel: "TikTok ads",
    percentage_spending: 20,
    percentage_views: 31,
    percentage_leads: 0,
    percentage_accounts: 20,
    percentage_revenue: 50,
  },
  {
    time: "Apr-15",
    channel: "Instagram Ads",
    percentage_spending: 4,
    percentage_views: 19,
    percentage_leads: 0,
    percentage_accounts: 30,
    percentage_revenue: 60,
  },
  {
    time: "Apr-15",
    channel: "Email",
    percentage_spending: 2,
    percentage_views: 4,
    percentage_leads: 0,
    percentage_accounts: 40,
    percentage_revenue: 10,
  },
  {
    time: "Apr-15",
    channel: "LinkedIn",
    percentage_spending: 4,
    percentage_views: 15,
    percentage_leads: 26,
    percentage_accounts: 10,
    percentage_revenue: 35,
  },
  {
    time: "Apr-15",
    channel: "Radio ads",
    percentage_spending: 3,
    percentage_views: 17,
    percentage_leads: 26,
    percentage_accounts: 10,
    percentage_revenue: 40,
  },
  {
    time: "Apr-15",
    channel: "TV ads",
    percentage_spending: 3,
    percentage_views: 13,
    percentage_leads: 26,
    percentage_accounts: 10,
    percentage_revenue: 30,
  },
  {
    time: "Apr-15",
    channel: "Google banner ads",
    percentage_spending: 4,
    percentage_views: 14,
    percentage_leads: 0,
    percentage_accounts: 10,
    percentage_revenue: 20,
  },
];

export default function StackedBarChart() {
  return (
    <section className="mt-6">
      <h2 className="mb-4 text-lg font-semibold">
        Stacked Bar Chart: Percentage Contribution by Channel
      </h2>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={rawData}
          margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
        >
          <XAxis dataKey="channel" angle={45} textAnchor="start" />
          <YAxis tickFormatter={(tick) => `${tick}%`} />
          <Tooltip />
          <Legend />

          <Bar
            dataKey="percentage_spending"
            stackId="a"
            fill="#8884d8"
            name="Spending"
          />
          <Bar
            dataKey="percentage_views"
            stackId="a"
            fill="#82ca9d"
            name="Views"
          />
          <Bar
            dataKey="percentage_leads"
            stackId="a"
            fill="#ffc658"
            name="Leads"
          />
          <Bar
            dataKey="percentage_accounts"
            stackId="a"
            fill="#d84d4d"
            name="New Accounts"
          />
          <Bar
            dataKey="percentage_revenue"
            stackId="a"
            fill="#4d79d8"
            name="Revenue"
          />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
