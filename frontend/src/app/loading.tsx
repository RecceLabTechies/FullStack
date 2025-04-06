'use client';

import { LoaderCircle } from 'lucide-react';

export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center" role="status" aria-live="polite">
      <div className="flex flex-col items-center space-y-4">
        <LoaderCircle className="h-8 w-8 animate-spin text-primary" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}
