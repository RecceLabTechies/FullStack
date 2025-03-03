"use client"

import { Card, CardContent } from "@/components/ui/card"

export default function KpiCards() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card className="bg-orange-400 text-white border-none">
        <CardContent className="p-4">
          <div className="text-3xl font-bold">$4654</div>
          <p className="text-sm mt-1">Revenue past month</p>
        </CardContent>
      </Card>

      <Card className="bg-orange-400 text-white border-none">
        <CardContent className="p-4">
          <div className="text-3xl font-bold">$6054</div>
          <p className="text-sm mt-1">Projected Revenue current month</p>
        </CardContent>
      </Card>

      <Card className="bg-green-400 text-white border-none">
        <CardContent className="p-4">
          <div className="text-3xl font-bold">4.3x</div>
          <p className="text-sm mt-1">ROI past month</p>
        </CardContent>
      </Card>

      <Card className="bg-green-400 text-white border-none">
        <CardContent className="p-4">
          <div className="text-3xl font-bold">4.3x</div>
          <p className="text-sm mt-1">Projected ROI</p>
        </CardContent>
      </Card>
    </div>
  )
}

