'use client';

import { useProphetPredictionsContext } from '@/context/prophet-predictions-context';
import { BrainCircuit } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function MetricsPredictedRevenueCard() {
  const { data, isLoading, error } = useProphetPredictionsContext();

  // Get the earliest prediction
  const earliestPrediction = data ? [...data].sort((a, b) => a.date - b.date)[0] : null;

  const formatRevenue = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <Card className="bg-neutral-100" aria-labelledby="predicted-revenue-title">
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className="rounded-full bg-orange-200 p-3">
            <BrainCircuit className="h-6 w-6" aria-hidden="true" />
          </div>
        </div>
        <div className="mt-4">
          {isLoading ? (
            <Skeleton className="h-8 w-32" aria-label="Loading predicted revenue data" />
          ) : error ? (
            <div className="text-sm text-destructive" role="alert">
              Failed to load prediction data
            </div>
          ) : (
            <>
              <h2 id="predicted-revenue-title" className="text-3xl font-bold">
                {earliestPrediction ? formatRevenue(earliestPrediction.revenue) : '$0'}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Predicted Revenue{' '}
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
