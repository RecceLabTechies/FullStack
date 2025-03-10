"use client";

import {
  Area,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const data = [
  { month: "Sep 24", revenue: 10.2, adSpend: 5.2 },
  { month: "Oct 24", revenue: 9.8, adSpend: 5.9 },
  { month: "Nov 24", revenue: 17.4, adSpend: 6.4 },
  { month: "Dec 24", revenue: 14.8, adSpend: 4.9 },
  { month: "Jan 24", revenue: 13.2, adSpend: 5.8, projected: true },
  { month: "Feb 24", revenue: 12.8, adSpend: 5.8, projected: true },
];

export default function RevenueChart() {
  return (
    <div>
      <h3 className="mb-4 text-lg font-medium">
        Revenue & Ad Spend across Months
      </h3>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <defs>
              <linearGradient id="projectedArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#d1fae5" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#d1fae5" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="month" />
            <YAxis
              domain={[0, 20]}
              tickCount={5}
              label={{
                value: "SGD (Thousands)",
                angle: -90,
                position: "insideLeft",
                style: { textAnchor: "middle" },
              }}
            />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="month"
              fill="url(#projectedArea)"
              stroke="transparent"
              activeDot={false}
              legendType="none"
              isAnimationActive={false}
              fillOpacity={1}
              data={data.filter((d) => d.projected)}
            />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="#f97316"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Revenue"
            />
            <Line
              type="monotone"
              dataKey="adSpend"
              stroke="#6b7280"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Ad Spend"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex justify-center gap-6">
        <div className="flex items-center">
          <div className="mr-2 h-4 w-4 rounded-full bg-orange-500"></div>
          <span>Revenue</span>
        </div>
        <div className="flex items-center">
          <div className="mr-2 h-4 w-4 rounded-full bg-gray-500"></div>
          <span>Ad Spend</span>
        </div>
        <div className="flex items-center">
          <div className="mr-2 h-4 w-4 rounded-sm bg-green-100"></div>
          <span>Projected Values</span>
        </div>
      </div>
    </div>
  );
}
