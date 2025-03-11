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
  { ageGroup: "18-24", value: 8.6, color: "#f97316" },
  { ageGroup: "25-34", value: 7.4, color: "#84cc16" },
  { ageGroup: "35-44", value: 5.2, color: "#eab308" },
  { ageGroup: "45-54", value: 3.8, color: "#6b7280" },
  { ageGroup: "55+", value: 2.1, color: "#8b5cf6" },
];

export default function AgeGroupBarChart() {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" tickFormatter={(value) => `${value}%`} />
        <YAxis dataKey="ageGroup" type="category" tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value: number) => [`${value}%`, "Percentage"]}
          labelFormatter={(label: string) => `Age Group: ${label}`}
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
