import { useEffect, useRef, useState } from 'react';

import { useProphetPredictionsContext } from '@/context/prophet-predictions-context';
import { Crown, Info, Loader2, Play } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardTitle } from '@/components/ui/card';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { Slider } from '@/components/ui/slider';

import { useProphetPipelineStatus, useProphetPipelineTrigger } from '@/hooks/use-backend-api';

export function MLTriggerCard() {
  const [forecastMonths, setForecastMonths] = useState(4);
  const { fetchPredictions } = useProphetPredictionsContext();
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

  const handleTriggerPipeline = async () => {
    try {
      lastProcessedTimestamp.current = null;
      await triggerPipeline(forecastMonths);
      toast.info(
        `Prophet ML prediction started for ${forecastMonths} month${forecastMonths > 1 ? 's' : ''}`
      );
      await checkStatus();
    } catch (error) {
      console.error('Failed to trigger pipeline:', error);
      toast.error(
        `Failed to trigger ML prediction: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  };

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (statusData?.is_running) {
      intervalId = setInterval(() => {
        void checkStatus();
      }, 2000); // Check status every 2 seconds
    }

    if (statusData?.last_prediction?.status === 'completed') {
      const currentTimestamp = statusData.last_prediction.timestamp;
      if (lastProcessedTimestamp.current !== currentTimestamp) {
        console.log('MLTriggerCard: Prediction completed, fetching new predictions');
        lastProcessedTimestamp.current = currentTimestamp;
        toast.success('Prophet ML prediction completed successfully!');
        void fetchPredictions();
      }
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [checkStatus, statusData?.is_running, statusData?.last_prediction, fetchPredictions]);

  return (
    <Card className="col-span-2" aria-labelledby="prophet-ml-title">
      <CardContent className="pt-6 flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-secondary p-3">
              <Crown size={24} aria-hidden="true" />
            </div>
            <CardTitle id="prophet-ml-title">Prophet ML</CardTitle>
          </div>
          <HoverCard>
            <HoverCardTrigger asChild>
              <Info
                className="h-4 w-4 text-muted-foreground cursor-help"
                aria-label="About Prophet ML Model"
              />
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
                <Info
                  className="h-4 w-4 text-muted-foreground cursor-help"
                  aria-label="About forecast duration"
                />
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
            aria-label={`Forecast duration: ${forecastMonths} months`}
            aria-valuemin={1}
            aria-valuemax={12}
            aria-valuenow={forecastMonths}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button
          onClick={handleTriggerPipeline}
          disabled={isTriggerLoading || isStatusLoading || statusData?.is_running}
          aria-busy={isTriggerLoading || isStatusLoading || statusData?.is_running}
        >
          {isTriggerLoading ? (
            <>
              <Play size={16} className="mr-2" aria-hidden="true" />
              <p>Starting...</p>
            </>
          ) : isStatusLoading ? (
            <>
              <Loader2 size={16} className="mr-2 animate-spin" aria-hidden="true" />
              <p>Checking...</p>
            </>
          ) : statusData?.is_running ? (
            <>
              <Loader2 size={16} className="mr-2 animate-spin" aria-hidden="true" />
              <p>Running...</p>
            </>
          ) : (
            <>
              <Play size={16} className="mr-2" aria-hidden="true" />
              <p>Run Prediction</p>
            </>
          )}
        </Button>

        {triggerError && (
          <p className="text-sm text-destructive" role="alert">
            Error triggering pipeline: {triggerError.message}
          </p>
        )}
      </CardFooter>
    </Card>
  );
}
