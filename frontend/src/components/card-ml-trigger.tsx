import { useEffect, useRef, useState } from 'react';

import { useProphetPredictionsContext } from '@/context/prophet-predictions-context';
import { Crown, Info, PlayCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardTitle } from '@/components/ui/card';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { Slider } from '@/components/ui/slider';

import { useProphetPipelineStatus, useProphetPipelineTrigger } from '@/hooks/use-backend-api';

export function MLTriggerCard() {
  const [forecastMonths, setForecastMonths] = useState(4);
  const { fetchPredictions } = useProphetPredictionsContext();
  // Track the last timestamp we responded to
  const lastProcessedTimestamp = useRef<number | null>(null);

  const {
    data: statusData,
    error: statusError,
    isLoading: isStatusLoading,
    checkStatus,
  } = useProphetPipelineStatus();

  const {
    error: triggerError,
    isLoading: isTriggerLoading,
    triggerPipeline,
  } = useProphetPipelineTrigger();

  // Function to handle pipeline trigger
  const handleTriggerPipeline = async () => {
    try {
      // Reset the last processed timestamp when starting a new prediction
      lastProcessedTimestamp.current = null;
      await triggerPipeline(forecastMonths);
      // Start polling for status
      await checkStatus();
    } catch (error) {
      console.error('Failed to trigger pipeline:', error);
    }
  };

  // Effect for polling status when needed
  useEffect(() => {
    // Check status immediately on mount
    void checkStatus();

    // Set up polling if prediction is running
    if (statusData?.is_running) {
      const intervalId = setInterval(() => {
        void checkStatus();
      }, 5000); // Poll every 5 seconds

      return () => clearInterval(intervalId);
    }
  }, [checkStatus, statusData?.is_running]);

  // Effect to fetch predictions when prediction completes
  useEffect(() => {
    // Skip if no status data or if it's not completed
    if (!statusData?.last_prediction || statusData.last_prediction.status !== 'completed') {
      return;
    }

    const currentTimestamp = statusData.last_prediction.timestamp;

    // If we've already processed this completed prediction, don't do it again
    if (lastProcessedTimestamp.current === currentTimestamp) {
      return;
    }

    console.log('MLTriggerCard: Prediction completed, fetching new predictions');
    // Update our reference to prevent future duplicate fetches
    lastProcessedTimestamp.current = currentTimestamp;
    // Fetch the predictions
    void fetchPredictions();
  }, [statusData?.last_prediction, fetchPredictions]);

  // Determine status display
  const getStatusDisplay = () => {
    if (isStatusLoading) {
      return <p className="text-muted-foreground">Checking status...</p>;
    }

    if (statusError) {
      return <p className="text-destructive">Error checking status</p>;
    }

    if (!statusData) {
      return <p className="text-muted-foreground">No status available</p>;
    }

    // Check for successful completion
    if (statusData.last_prediction?.status === 'completed') {
      return <p className="text-muted-foreground">Prophet ML is idle</p>;
    }

    if (statusData.is_running) {
      return <p className="text-green-500">Prophet ML is running...</p>;
    }

    // Check specific statuses
    switch (statusData.status) {
      case 'error':
        return <p className="text-destructive">Error: {statusData.message}</p>;
      case 'idle':
        return <p className="text-muted-foreground">Ready to start prediction</p>;
      case 'skipped':
        return <p className="text-amber-500">Prediction skipped: {statusData.message}</p>;
      case 'lock_failed':
        return <p className="text-amber-500">Unable to start: {statusData.message}</p>;
      default:
        return <p className="text-muted-foreground">{statusData.message || 'Unknown status'}</p>;
    }
  };

  return (
    <Card className="col-span-2">
      <CardContent className="pt-6 flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-secondary p-3">
              <Crown size={24} />
            </div>
            <CardTitle>Prophet ML</CardTitle>
          </div>
          <HoverCard>
            <HoverCardTrigger asChild>
              <Info className="h-4 w-4 text-muted-foreground cursor-help" />
            </HoverCardTrigger>
            <HoverCardContent className="w-80">
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Prophet ML Model</h4>
                <p className="text-sm text-muted-foreground">
                  This triggers Facebook&apos;s Prophet machine learning model to analyze your
                  historical advertising data and generate predictions for future revenue, ad spend,
                  and ROI. The model identifies patterns and trends to help optimize your
                  advertising strategy.
                </p>
              </div>
            </HoverCardContent>
          </HoverCard>
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Forecast duration: {forecastMonths} month{forecastMonths > 1 ? 's' : ''}
            </div>
            <HoverCard>
              <HoverCardTrigger asChild>
                <Info className="h-4 w-4 text-muted-foreground cursor-help" />
              </HoverCardTrigger>
              <HoverCardContent className="w-80">
                <p className="text-sm text-muted-foreground">
                  Select how many months into the future you want the prediction to forecast. Longer
                  ranges may take more time to calculate.
                </p>
              </HoverCardContent>
            </HoverCard>
          </div>
          <Slider
            min={1}
            max={12}
            step={1}
            value={[forecastMonths]}
            onValueChange={(value) => setForecastMonths(value[0] ?? 4)}
          />
          <div className="text-sm text-muted-foreground mt-1">{getStatusDisplay()}</div>
          <Button
            onClick={handleTriggerPipeline}
            disabled={isTriggerLoading || isStatusLoading || statusData?.is_running}
          >
            <PlayCircle className="mr-2 h-4 w-4" />
            Run Prediction
          </Button>

          {triggerError && (
            <div className="text-sm text-destructive">
              Error triggering pipeline: {triggerError.message}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
