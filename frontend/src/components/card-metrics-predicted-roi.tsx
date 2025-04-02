'use client';

import { useProphetPredictionsContext } from '@/context/prophet-predictions-context';
import { TrendingUp } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function MetricsPredictedROICard() {
  const { data, isLoading, error } = useProphetPredictionsContext();

  // Get the earliest prediction
  const earliestPrediction = data ? [...data].sort((a, b) => a.date - b.date)[0] : null;

  // Calculate ROI
  const roi = earliestPrediction
    ? ((earliestPrediction.revenue - earliestPrediction.ad_spend) / earliestPrediction.ad_spend) *
      100
    : 0;

  return (
    <Card className="bg-neutral-100">
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className="rounded-full bg-orange-200 p-3">
            <TrendingUp className="h-6 w-6" />
          </div>
        </div>
        <div className="mt-4">
          {isLoading ? (
            <Skeleton className="h-8 w-32" />
          ) : error ? (
            <div className="text-sm text-destructive">Failed to load prediction data</div>
          ) : (
            <>
              <h2 className="text-3xl font-bold">{roi.toFixed(1)}%</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Predicted ROI{' '}
                {earliestPrediction
                  ? new Date(earliestPrediction.date * 1000).toLocaleDateString('default', {
                      month: 'long',
                      year: 'numeric',
                    })
                  : ''}
              </p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
