import { useEffect } from 'react';

import { useDatabaseOperations } from '@/context/database-operations-context';
import { CircleDollarSign } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

import { useLatestMonthRevenue } from '@/hooks/use-backend-api';

export function MetricsRevenueCard() {
  const { data, isLoading, error, fetchLatestMonthRevenue } = useLatestMonthRevenue();
  const { lastUpdated } = useDatabaseOperations();

  useEffect(() => {
    void fetchLatestMonthRevenue();
  }, [fetchLatestMonthRevenue, lastUpdated]);

  const formatRevenue = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getMonthName = (month: number) => {
    return new Intl.DateTimeFormat('en-US', { month: 'long' }).format(new Date(2024, month - 1));
  };

  return (
    <Card aria-labelledby="revenue-title">
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className="rounded-full bg-secondary p-3">
            <CircleDollarSign className="h-6 w-6" aria-hidden="true" />
          </div>
        </div>
        <div className="mt-4">
          {isLoading ? (
            <Skeleton className="h-8 w-32" aria-label="Loading revenue data" />
          ) : error ? (
            <div className="text-sm text-destructive" role="alert">
              Failed to load revenue data
            </div>
          ) : (
            <>
              <h2 id="revenue-title" className="text-3xl font-bold">
                {formatRevenue(data?.revenue ?? 0)}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Revenue{' '}
                {data?.month && data?.year ? `${getMonthName(data.month)} ${data.year}` : ''}
              </p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
