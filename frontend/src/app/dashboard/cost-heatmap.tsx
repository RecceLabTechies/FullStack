"use client";

import { useEffect, useState } from "react";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";
import { fetchCostHeatmapData, CostHeatmapData } from "@/api/dbApi";

export default function CostTable() {
  const [data, setData] = useState<CostHeatmapData[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      const result = await fetchCostHeatmapData();
      if (result) {
        setData(result);
        console.log(result);
      } else {
        setError("Failed to load data.");
      }
      setLoading(false);
    };

    loadData();
  }, []);

  return (
    <section className="mt-6">
      <h2 className="mb-4 text-lg font-semibold">Cost Table</h2>

      {loading && <p>Loading data...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && data && (
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
                <TableCell className="text-center">
                  {row.costPerLead.toFixed(4)}
                </TableCell>
                <TableCell className="text-center">
                  {row.costPerView.toFixed(4)}
                </TableCell>
                <TableCell className="text-center">
                  {row.costPerAccount.toFixed(4)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </section>
  );
}
