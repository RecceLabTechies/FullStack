import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { BarChart, DollarSign, TrendingDown, TrendingUp } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string;
  trend?: number;
  icon: React.ReactNode;
  loading?: boolean;
}

function KpiCard({ title, value, trend, icon, loading = false }: KpiCardProps) {
  return (
    <Card
      className={cn(
        "transition-all duration-200 hover:shadow-md",
        loading && "animate-pulse",
      )}
    >
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="rounded-full bg-primary/10 p-2 text-primary">
            {icon}
          </div>
          {trend !== undefined && (
            <div
              className={cn(
                "flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium",
                trend >= 0
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700",
              )}
            >
              {trend >= 0 ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              {Math.abs(trend)}%
            </div>
          )}
        </div>
        <div className="mt-4">
          <div className="text-4xl font-bold tracking-tight">{value}</div>
          <p className="mt-2 text-sm text-muted-foreground">{title}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function KpiCards() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <KpiCard
        title="Revenue past month"
        value="$4,654"
        trend={12}
        icon={<DollarSign className="h-4 w-4" />}
      />
      <KpiCard
        title="Projected Revenue"
        value="$6,054"
        trend={8}
        icon={<BarChart className="h-4 w-4" />}
      />
      <KpiCard
        title="ROI past month"
        value="4.3x"
        trend={-2}
        icon={<TrendingUp className="h-4 w-4" />}
      />
      <KpiCard
        title="Projected ROI"
        value="4.3x"
        trend={5}
        icon={<BarChart className="h-4 w-4" />}
      />
    </div>
  );
}
