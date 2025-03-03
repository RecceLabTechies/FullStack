"use client"

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

const data = [
  { ageGroup: "18-24", value: 8.6, color: "#f97316" },
  { ageGroup: "25-34", value: 7.4, color: "#84cc16" },
  { ageGroup: "35-54", value: 3.4, color: "#eab308" },
  { ageGroup: "45-54", value: 1.6, color: "#6b7280" },
]

export default function AgeGroupBarChart() {
  return (
    <div>
      <h3 className="text-lg font-medium mb-4">Age Group: Revenue per Dollar spend</h3>
      <div className="h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
            <XAxis type="number" domain={[0, 10]} />
            <YAxis dataKey="ageGroup" type="category" width={60} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => [`${value}`, "Value"]} labelFormatter={(label) => `Age Group: ${label}`} />
            <Bar dataKey="value" fill="#f97316" radius={[0, 4, 4, 0]} barSize={30} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap justify-center mt-2 gap-2">
        {data.map((item) => (
          <div key={item.ageGroup} className="flex items-center">
            <div className="w-3 h-3 rounded-full mr-1" style={{ backgroundColor: item.color }}></div>
            <span className="text-xs">{item.ageGroup}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

