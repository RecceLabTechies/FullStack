"use client";

import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useState } from "react";

const initialData = [
  { channel: "Instagram", spend: 7.5 },
  { channel: "Newspaper ads", spend: 6.3 },
  { channel: "LinkedIn", spend: 7.5 },
  { channel: "Google banner", spend: 3.0 },
  { channel: "Mail", spend: 7.9 },
  { channel: "Facebook ads", spend: 2.2 },
  { channel: "Influencer", spend: 0.5 },
  { channel: "Radio ads", spend: 6.3 },
];

export default function AdSpendTable() {
  const [adSpendData, setAdSpendData] = useState(initialData);

  const handleSpendChange = (index: number, value: string) => {
    const newData = [...adSpendData];
    if (newData[index]) {
      newData[index].spend = Number.parseFloat(value) || 0;
      setAdSpendData(newData);
    }
  };

  return (
    <div>
      <h3 className="mb-4 text-lg font-medium">
        Enter your budgeted ad spend for predictions across the next month
        (thousands $GD)
      </h3>
      <div className="overflow-hidden rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              {adSpendData.map((item) => (
                <TableHead key={item.channel} className="text-center">
                  {item.channel}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              {adSpendData.map((item, index) => (
                <TableCell key={item.channel} className="text-center">
                  <Input
                    type="number"
                    value={item.spend}
                    onChange={(e) => handleSpendChange(index, e.target.value)}
                    className="w-full text-center"
                  />
                </TableCell>
              ))}
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
