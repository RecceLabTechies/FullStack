"use client";

import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";

// include age group toggle button and other filter buttons
const data = [
  {
    channel: "Influencer",
    costPerLead: 0.001,
    costPerView: 0.004,
    costPerAccount: 0.008,
  },
  {
    channel: "Sponsored search ads",
    costPerLead: 0.001,
    costPerView: 0.0026,
    costPerAccount: 0.004,
  },
  {
    channel: "TikTok ads",
    costPerLead: 0.0005,
    costPerView: 0.0016,
    costPerAccount: 0.0025,
  },
  {
    channel: "Instagram Ads",
    costPerLead: 0.001,
    costPerView: 0.0021,
    costPerAccount: 0.0013,
  },
  {
    channel: "Email",
    costPerLead: 0.003,
    costPerView: 0.005,
    costPerAccount: 0.0005,
  },
  {
    channel: "LinkedIn",
    costPerLead: 0.0015,
    costPerView: 0.0026,
    costPerAccount: 0.004,
  },
];

const getHeatmapColor = (value: number, max: number) => {
  const intensity = Math.round((value / max) * 255);
  return `rgb(255, ${255 - intensity}, ${255 - intensity})`; // Red intensity based on value
};

export default function CostHeatmapTable() {
  const maxCost = {
    costPerLead: Math.max(...data.map((d) => d.costPerLead)),
    costPerView: Math.max(...data.map((d) => d.costPerView)),
    costPerAccount: Math.max(...data.map((d) => d.costPerAccount)),
  };

  return (
    <section className="mt-6">
      <h2 className="mb-4 text-lg font-semibold">Cost Heatmap</h2>
      <Table className="border">
        <TableHeader>
          <TableRow className="bg-gray-200">
            <TableHead>Channel</TableHead>
            <TableHead className="text-center">Cost Per Lead</TableHead>
            <TableHead className="text-center">Cost Per View</TableHead>
            <TableHead className="text-center">Cost Per Account</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow key={row.channel}>
              <TableCell className="font-medium">{row.channel}</TableCell>
              <TableCell
                className="text-center"
                style={{
                  backgroundColor: getHeatmapColor(
                    row.costPerLead,
                    maxCost.costPerLead,
                  ),
                }}
              >
                {row.costPerLead.toFixed(4)}
              </TableCell>
              <TableCell
                className="text-center"
                style={{
                  backgroundColor: getHeatmapColor(
                    row.costPerView,
                    maxCost.costPerView,
                  ),
                }}
              >
                {row.costPerView.toFixed(4)}
              </TableCell>
              <TableCell
                className="text-center"
                style={{
                  backgroundColor: getHeatmapColor(
                    row.costPerAccount,
                    maxCost.costPerAccount,
                  ),
                }}
              >
                {row.costPerAccount.toFixed(4)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </section>
  );
}
