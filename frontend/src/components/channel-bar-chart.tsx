"use client"

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

const data = [
  { channel: "Instagram", value: 10.2, color: "#f97316" },
  { channel: "Email", value: 7.6, color: "#84cc16" },
  { channel: "Google Banner Ads", value: 4.6, color: "#eab308" },
  { channel: "Influencer", value: 3.4, color: "#6b7280" },
]

export default function ChannelBarChart() {
  return (
    <div>
      <h3 className="text-lg font-medium mb-4">Channels: Revenue per Dollar spend</h3>
      <div className="h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
            <XAxis type="number" domain={[0, 12]} />
            <YAxis dataKey="channel" type="category" width={100} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => [`${value}`, "Value"]} labelFormatter={(label) => `Channel: ${label}`} />
            <Bar dataKey="value" fill="#f97316" radius={[0, 4, 4, 0]} barSize={30} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap justify-center mt-2 gap-2">
        {data.map((item) => (
          <div key={item.channel} className="flex items-center">
            <div className="w-3 h-3 rounded-full mr-1" style={{ backgroundColor: item.color }}></div>
            <span className="text-xs">{item.channel}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

