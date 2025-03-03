"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const predictionData = [
  { period: "Predicted Time Period", t1: "", t2: "", t3: "", t4: "", className: "bg-gray-600 text-white" },
  { period: "High", t1: "14.8", t2: "14.6", t3: "15.6", t4: "15.0", className: "bg-gray-200" },
  { period: "Low", t1: "11.5", t2: "11.9", t3: "11.0", t4: "11.0", className: "bg-amber-200" },
]

export default function PredictionTable() {
  return (
    <div>
      <div className="bg-white rounded-lg overflow-hidden border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-1/5"></TableHead>
              <TableHead className="text-center">Projected T+1 Month</TableHead>
              <TableHead className="text-center">Projected T+2 Month</TableHead>
              <TableHead className="text-center">Projected T+3 Month</TableHead>
              <TableHead className="text-center">Projected T+4 Month</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {predictionData.map((row, index) => (
              <TableRow key={index}>
                <TableCell className={row.className}>{row.period}</TableCell>
                <TableCell className={row.className + " text-center"}>{row.t1}</TableCell>
                <TableCell className={row.className + " text-center"}>{row.t2}</TableCell>
                <TableCell className={row.className + " text-center"}>{row.t3}</TableCell>
                <TableCell className={row.className + " text-center"}>{row.t4}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="mt-2 text-xs text-gray-600">
        *High, Low corresponds to 95%, 5% threshold of predicted values respectively
      </div>
    </div>
  )
}

