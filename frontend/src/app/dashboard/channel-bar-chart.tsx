import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const data = [
  { channel: "Instagram", value: 10.2, color: "#f97316" },
  { channel: "Email", value: 7.6, color: "#84cc16" },
  { channel: "Google Banner Ads", value: 4.6, color: "#eab308" },
  { channel: "Influencer", value: 3.4, color: "#6b7280" },
  { channel: "Referral", value: 2.8, color: "#8b5cf6" },
];

export default function ChannelBarChart() {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" tickFormatter={(value) => `${value}%`} />
        <YAxis dataKey="channel" type="category" tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value: number) => [`${value}%`, "Conversion Rate"]}
          labelFormatter={(label: string) => `Channel: ${label}`}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={30}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
