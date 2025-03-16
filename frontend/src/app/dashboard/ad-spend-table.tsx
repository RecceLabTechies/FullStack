"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Info, RefreshCw } from "lucide-react";
import { useState } from "react";

interface AdSpendItem {
  channel: string;
  spend: number;
  description?: string;
}

interface PredictionData {
  period: "High" | "Low";
  values: number[];
}

const initialAdSpend: AdSpendItem[] = [
  {
    channel: "Instagram",
    spend: 7.5,
    description: "Social media advertising on Instagram platform",
  },
  {
    channel: "Newspaper ads",
    spend: 6.3,
    description: "Traditional print media advertising",
  },
  {
    channel: "LinkedIn",
    spend: 7.5,
    description: "Professional network advertising",
  },
  {
    channel: "Google banner",
    spend: 3.0,
    description: "Display advertising on Google network",
  },
  {
    channel: "Mail",
    spend: 7.9,
    description: "Direct mail marketing campaigns",
  },
  {
    channel: "Facebook ads",
    spend: 2.2,
    description: "Social media advertising on Facebook",
  },
  {
    channel: "Influencer",
    spend: 0.5,
    description: "Influencer marketing partnerships",
  },
  {
    channel: "Radio ads",
    spend: 6.3,
    description: "Traditional radio advertising",
  },
];

const initialPredictions: PredictionData[] = [
  { period: "High", values: [14.8, 14.6, 15.6, 15.0] },
  { period: "Low", values: [11.5, 11.9, 11.0, 11.0] },
];

export default function AdSpendAndPredictionTable() {
  const [adSpendData, setAdSpendData] = useState<AdSpendItem[]>(initialAdSpend);
  const [predictions, setPredictions] =
    useState<PredictionData[]>(initialPredictions);
  const [isLoading, setIsLoading] = useState(false);

  const handleSpendChange = (index: number, value: string) => {
    const newData = [...adSpendData];
    if (newData[index]) {
      const parsedValue = Math.max(0, Number.parseFloat(value) || 0);
      newData[index].spend = Number(parsedValue.toFixed(2));
      setAdSpendData(newData);
    }
  };

  const totalSpend = adSpendData.reduce((sum, item) => sum + item.spend, 0);

  const handleUpdatePredictions = async () => {
    setIsLoading(true);
    try {
      // TODO: Replace with actual API call
      // const response = await fetch('/api/predictions', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ adSpend: adSpendData }),
      // });
      // const newPredictions = await response.json();
      // setPredictions(newPredictions);

      // Simulated delay for now
      await new Promise((resolve) => setTimeout(resolve, 1000));
      // In the real implementation, this would be replaced with actual API data
    } catch (error) {
      console.error("Failed to update predictions:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="space-y-8">
      {/* Ad Spend Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-lg font-medium">
            Monthly Ad Spend Budget
          </CardTitle>
          <div className="text-sm text-muted-foreground">
            Total: ${totalSpend.toFixed(2)}k
          </div>
        </CardHeader>
        <CardContent>
          <section className="rounded-lg border bg-card">
            <div className="p-1">
              <Table>
                <TableHeader>
                  <TableRow>
                    {adSpendData.map((item) => (
                      <TableHead key={item.channel} className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          {item.channel}
                          {item.description && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Info className="h-4 w-4 text-muted-foreground" />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>{item.description}</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </div>
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    {adSpendData.map((item, index) => (
                      <TableCell key={item.channel} className="p-2 text-center">
                        <div className="relative">
                          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                            $
                          </span>
                          <Input
                            type="number"
                            value={item.spend}
                            onChange={(e) =>
                              handleSpendChange(index, e.target.value)
                            }
                            className="pl-6 text-center"
                            min="0"
                            step="0.1"
                          />
                        </div>
                      </TableCell>
                    ))}
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </section>
          <footer className="mt-4 flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Enter your budgeted ad spend for predictions across the next month
              (thousands $GD)
            </p>
            <Button
              onClick={handleUpdatePredictions}
              disabled={isLoading}
              className="ml-4"
            >
              {isLoading ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Update Predictions
            </Button>
          </footer>
        </CardContent>
      </Card>

      {/* Predictions Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-medium">
            Revenue Predictions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <section className="overflow-hidden rounded-lg border bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-1/5 bg-gray-50"></TableHead>
                  {[1, 2, 3, 4].map((month) => (
                    <TableHead key={month} className="bg-gray-50 text-center">
                      Projected T+{month} Month
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {predictions.map((row, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{row.period}</TableCell>
                    {row.values.map((value, idx) => (
                      <TableCell
                        key={idx}
                        className={`text-center ${
                          row.period === "High"
                            ? "text-red-600"
                            : "text-blue-600"
                        }`}
                      >
                        {value.toFixed(1)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </section>
          <footer className="mt-3 text-sm text-gray-600">
            <span className="font-medium">Note:</span> High and Low values
            represent the 95% and 5% threshold of predicted values respectively
          </footer>
        </CardContent>
      </Card>
    </section>
  );
}
