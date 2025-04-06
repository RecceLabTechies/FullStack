'use client';

import { useProphetPredictionsContext } from '@/context/prophet-predictions-context';
import { Info, TrendingUp } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
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
    <Card className="bg-neutral-100" aria-labelledby="predicted-roi-title">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-orange-200 p-3">
              <TrendingUp className="h-6 w-6" aria-hidden="true" />
            </div>
          </div>
          <HoverCard>
            <HoverCardTrigger asChild>
              <Info
                className="h-4 w-4 text-muted-foreground cursor-help"
                aria-label="Predicted ROI information"
              />
            </HoverCardTrigger>
            <HoverCardContent className="w-80">
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Predicted Return on Investment (ROI)</h4>
                <p className="text-sm text-muted-foreground">
                  Forecasted ROI for upcoming periods, calculated using the same formula:
                  ((Predicted Revenue - Predicted Ad Spend) / Predicted Ad Spend) × 100. This
                  prediction helps in planning future advertising investments.
                </p>
              </div>
            </HoverCardContent>
          </HoverCard>
        </div>
        <div className="mt-4">
          {isLoading ? (
            <Skeleton className="h-8 w-32" aria-label="Loading predicted ROI data" />
          ) : error ? (
            <div className="text-sm text-destructive" role="alert">
              Failed to load prediction data
            </div>
          ) : (
            <>
              <h2 id="predicted-roi-title" className="text-3xl font-bold">
                {roi.toFixed(1)}%
              </h2>
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
