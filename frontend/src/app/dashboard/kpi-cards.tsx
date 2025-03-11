"use client";

import { Card, CardContent } from "@/components/ui/card";

export default function KpiCards() {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <Card className="bg-muted">
        <CardContent className="p-4">
          <div className="text-3xl font-bold">$4654</div>
          <p className="mt-1 text-sm">Revenue past month</p>
        </CardContent>
      </Card>
      <Card className="bg-muted">
        <CardContent className="p-4">
          <div className="text-3xl font-bold">$6054</div>
          <p className="mt-1 text-sm">Projected Revenue current month</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="text-3xl font-bold">4.3x</div>
          <p className="mt-1 text-sm">ROI past month</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="text-3xl font-bold">4.3x</div>
          <p className="mt-1 text-sm">Projected ROI</p>
        </CardContent>
      </Card>
    </div>
  );
}
