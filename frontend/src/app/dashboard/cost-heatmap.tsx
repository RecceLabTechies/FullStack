"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Button } from "@/components/ui/button";

// cannot install plotly pls help
const data = [
  {
    time: "Apr-15",
    ageGroup: "18-24",
    channel: "Influencer",
    costPerLead: 0.001,
    costPerView: 0.004,
    costPerAccount: 0.008,
  },
  {
    time: "Apr-15",
    ageGroup: "18-24",
    channel: "Sponsored search ads",
    costPerLead: 0.001,
    costPerView: 0.0026,
    costPerAccount: 0.004,
  },
  {
    time: "Apr-15",
    ageGroup: "18-24",
    channel: "TikTok ads",
    costPerLead: 0.0005,
    costPerView: 0.0016,
    costPerAccount: 0.0025,
  },
  {
    time: "Apr-15",
    ageGroup: "18-24",
    channel: "Instagram Ads",
    costPerLead: 0.001,
    costPerView: 0.0021,
    costPerAccount: 0.0013,
  },
  {
    time: "Apr-15",
    ageGroup: "18-24",
    channel: "Email",
    costPerLead: 0.003,
    costPerView: 0.005,
    costPerAccount: 0.0005,
  },
  {
    time: "Apr-15",
    ageGroup: "18-24",
    channel: "LinkedIn",
    costPerLead: 0.0015,
    costPerView: 0.0026,
    costPerAccount: 0.004,
  },
];

export default function CostBarChart() {
  const [viewBy, setViewBy] = useState<"channel" | "ageGroup">("channel");

  return (
    <section className="mt-6">
      <div className="mb-4 flex items-center justify-between">
        <Button
          onClick={() =>
            setViewBy(viewBy === "channel" ? "ageGroup" : "channel")
          }
        >
          Toggle View ({viewBy === "channel" ? "Age Group" : "Channel"})
        </Button>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
        >
          <XAxis dataKey={viewBy} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="costPerLead" fill="#8884d8" name="Cost Per Lead" />
          <Bar dataKey="costPerView" fill="#82ca9d" name="Cost Per View" />
          <Bar
            dataKey="costPerAccount"
            fill="#ffc658"
            name="Cost Per Account"
          />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
