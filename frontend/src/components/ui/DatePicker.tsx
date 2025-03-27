"use client"

import { Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface DatePickerProps {
  dateMode: "single" | "range";
  setDateMode: (mode: "single" | "range") => void;
  singleDate: { year: string; month: string };
  setSingleDate: (date: { year: string; month: string }) => void;
  fromDate: string;
  toDate: string;
  setFromDate: (date: string) => void;
  setToDate: (date: string) => void;
  onApply: () => void;
}

export default function DatePicker({
  dateMode,
  setDateMode,
  singleDate,
  setSingleDate,
  fromDate,
  toDate,
  setFromDate,
  setToDate,
  onApply, // ✅ must be included here
}: DatePickerProps) {
  const isApplyDisabled =
    (dateMode === "single" && !singleDate.year) ||
    (dateMode === "range" && (!fromDate || !toDate))

  const handleApply = () => {
    onApply(); // ✅ this now works because it's inside the component
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Date Selection
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={dateMode} onValueChange={(value) => setDateMode(value as "single" | "range")}>
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="single">Single Date</TabsTrigger>
            <TabsTrigger value="range">Date Range</TabsTrigger>
          </TabsList>

          <TabsContent value="single">
            <div className="w-full">
              <label className="block text-sm font-medium mb-1">Select Date</label>
              <div className="flex gap-2">
                <div className="w-1/2">
                  <select
                    value={singleDate.year}
                    onChange={(e) => setSingleDate({ ...singleDate, year: e.target.value })}
                    className="w-full border rounded px-2 py-1"
                  >
                    <option value="">Year</option>
                    {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map((year) => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="w-1/2">
                  <select
                    value={singleDate.month}
                    onChange={(e) => setSingleDate({ ...singleDate, month: e.target.value })}
                    className="w-full border rounded px-2 py-1"
                    disabled={!singleDate.year}
                  >
                    <option value="">Month</option>
                    {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => (
                      <option key={month} value={month}>
                        {new Date(2000, month - 1, 1).toLocaleString("default", { month: "long" })}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="range">
            <section className="flex gap-2 flex-1">
              <div className="w-full">
                <label className="block text-sm font-medium mb-1">From</label>
                <input
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  className="w-full border rounded px-2 py-1"
                />
              </div>
              <div className="w-full">
                <label className="block text-sm font-medium mb-1">To</label>
                <input
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  className="w-full border rounded px-2 py-1"
                />
              </div>
            </section>
          </TabsContent>
        </Tabs>

        <div className="mt-4">
          <Button className="w-full" disabled={isApplyDisabled} onClick={handleApply}>
            Apply
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

