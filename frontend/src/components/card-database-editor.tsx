'use client';

import { useCallback, useEffect, useState } from 'react';

import { Trash2 } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

import { useDatabases, useDeleteDatabase } from '@/hooks/use-backend-api';

export default function DatabaseEditorCard() {
  // Database state
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');

  // Database hooks
  const { data: databases, fetchDatabases, isLoading: isFetching } = useDatabases();
  const { deleteDatabase, isLoading: isDeleting } = useDeleteDatabase();

  // Load databases on mount
  useEffect(() => {
    void fetchDatabases();
  }, [fetchDatabases]);

  // Handle database deletion
  const handleDelete = useCallback(
    async (dbName: string) => {
      try {
        await deleteDatabase(dbName);
        toast.success(`Database "${dbName}" cleared successfully`);
        setSelectedDatabase('');
        void fetchDatabases();
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        toast.error(`Failed to clear database: ${errorMessage}`);
      }
    },
    [deleteDatabase, fetchDatabases]
  );

  return (
    <>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Clean Databases</h3>
      </div>

      {/* Database Selection and Actions */}

      <div className="space-y-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-between"
              disabled={isFetching || !databases?.length}
            >
              {selectedDatabase || 'Select a database'}
              {isFetching ? (
                <span className="animate-pulse">Loading...</span>
              ) : (
                <span className="text-muted-foreground">{databases?.length ?? 0} available</span>
              )}
            </Button>
          </DropdownMenuTrigger>

          <DropdownMenuContent className="w-full max-h-60 overflow-y-auto">
            {databases?.map((db) => (
              <DropdownMenuItem
                key={db}
                onSelect={() => setSelectedDatabase(db)}
                className="cursor-pointer flex justify-between items-center"
              >
                {db}
                <Button
                  variant="destructive"
                  size="icon"
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    void handleDelete(db); // Pass database name directly
                  }}
                >
                  <Trash2 size={18} />
                </Button>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </>
  );
}
