'use client';

import React, { useCallback, useState } from 'react';

import { type DbStructure } from '@/types/types';
import { LoaderCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

import { useCsvUpload, useDbStructure } from '@/hooks/use-backend-api';

// Common types
type CollectionDocument = Record<string, unknown>;

const StatusMessage = ({
  message,
  type,
}: {
  message: string;
  type: 'success' | 'error' | 'info';
}) => {
  const styles = {
    success: 'bg-primary/10 text-primary',
    error: 'bg-destructive/15 text-destructive',
    info: 'text-muted-foreground',
  };

  return <div className={`rounded-md p-3 ${styles[type]}`}>{message}</div>;
};

// Collection table component
const CollectionTable = ({ collection }: { collection: CollectionDocument[] }) => {
  if (!collection.length) return null;

  const headers = Object.keys(collection[0] ?? {});

  // Helper to format cell values
  const formatCellValue = (value: unknown, key: string) => {
    if (typeof value !== 'object' || value === null) return String(value);

    // Handle MongoDB ObjectId
    if (key === '_id' && value !== null && typeof value === 'object' && '$oid' in value) {
      return (value as { $oid: string }).$oid;
    }

    return JSON.stringify(value);
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {headers.map((key) => (
            <TableHead key={key}>{key}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {collection.map((doc, index) => (
          <TableRow key={index}>
            {Object.entries(doc).map(([key, value]) => (
              <TableCell key={key}>{formatCellValue(value, key)}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

// Database structure component
const DatabaseStructure = ({ dbStructure }: { dbStructure: DbStructure }) => (
  <div className="mt-6 space-y-6">
    {Object.entries(dbStructure).map(([dbName, collections]) => (
      <Card key={dbName}>
        <CardHeader>
          <h2 className="text-xl">{dbName}</h2>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(collections as Record<string, CollectionDocument[] | string>).map(
              ([collectionName, collection]) => (
                <div key={collectionName} className="space-y-2">
                  <h3 className="text-lg font-semibold">Collection: {collectionName}</h3>
                  {typeof collection === 'string' ? (
                    <p className="text-muted-foreground">{collection}</p>
                  ) : Array.isArray(collection) && collection.length > 0 ? (
                    <CollectionTable collection={collection} />
                  ) : (
                    <p className="text-muted-foreground">No data available</p>
                  )}
                </div>
              )
            )}
          </div>
        </CardContent>
      </Card>
    ))}
  </div>
);

// Upload button component
const UploadButton = ({ onUploadSuccess }: { onUploadSuccess?: () => void }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<{
    message: string | null;
    type: 'success' | 'error' | 'info';
  }>({ message: null, type: 'info' });
  const { uploadCsv, isLoading: isUploading, data } = useCsvUpload();
  const lastProcessedData = React.useRef<typeof data>(null);

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setUploadState({ message: null, type: 'info' });
    lastProcessedData.current = null;
  }, []);

  const handleUpload = useCallback(async () => {
    if (!selectedFile) {
      setUploadState({
        message: 'Please select a CSV file.',
        type: 'error',
      });
      return;
    }

    if (!selectedFile.name.endsWith('.csv')) {
      setUploadState({
        message: 'Only CSV files are accepted.',
        type: 'error',
      });
      return;
    }

    setUploadState({
      message: 'Uploading...',
      type: 'info',
    });
    lastProcessedData.current = null;

    try {
      await uploadCsv(selectedFile);
    } catch (error) {
      console.error('Error uploading file:', error);
      setUploadState({
        message: `Error uploading file: ${error instanceof Error ? error.message : 'Unknown error'}`,
        type: 'error',
      });
    }
  }, [selectedFile, uploadCsv]);

  // Handle successful upload
  React.useEffect(() => {
    if (data && data !== lastProcessedData.current) {
      lastProcessedData.current = data;
      setUploadState({
        message: `Success: Uploaded ${data.count} records to ${data.collection}`,
        type: 'success',
      });
      setSelectedFile(null);

      // Reset file input
      const fileInput = document.querySelector<HTMLInputElement>('input[type="file"]');
      if (fileInput) fileInput.value = '';

      onUploadSuccess?.();
    }
  }, [data, onUploadSuccess]);

  return (
    <div className="space-y-4">
      <div className="grid w-full max-w-sm items-center gap-1.5">
        <Label htmlFor="csv-file">CSV File</Label>
        <Input
          id="csv-file"
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          disabled={isUploading}
          className="cursor-pointer"
        />
      </div>
      <Button
        onClick={handleUpload}
        disabled={isUploading || !selectedFile}
        className="w-full sm:w-auto"
      >
        {isUploading ? (
          <>
            <LoaderCircle size={24} className="animate-spin" />
            <span className="ml-2">Uploading...</span>
          </>
        ) : (
          'Upload CSV'
        )}
      </Button>
      {uploadState.message && (
        <StatusMessage message={uploadState.message} type={uploadState.type} />
      )}
    </div>
  );
};

// Main component
export default function DatabaseHelper() {
  const { data: dbStructure, isLoading, error, fetchStructure } = useDbStructure();

  React.useEffect(() => {
    void fetchStructure();
  }, [fetchStructure]); // Empty dependency array to run only once

  return (
    <main className="container mx-auto flex-1 space-y-4 p-4 pt-6 md:p-8">
      <header className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Mongo Manager</h1>
      </header>

      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Database Structure</CardTitle>
            <CardDescription>
              View and manage your database collections and documents.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading && (
              <div className="flex items-center space-x-4">
                <LoaderCircle size={24} className="animate-spin" />
                <p className="text-muted-foreground">Loading database structure...</p>
              </div>
            )}
            {error && <StatusMessage message={error.message} type="error" />}
            {dbStructure && (
              <StatusMessage message="Database structure loaded successfully!" type="success" />
            )}
            {dbStructure && <DatabaseStructure dbStructure={dbStructure} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
            <CardDescription>Refresh the database structure or upload new data.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={() => void fetchStructure()}
              disabled={isLoading}
              variant="secondary"
              className="w-full sm:w-auto"
            >
              {isLoading ? (
                <>
                  <LoaderCircle size={24} className="animate-spin" />
                  <span className="ml-2">Refreshing...</span>
                </>
              ) : (
                'Refresh Database Structure'
              )}
            </Button>
            <UploadButton onUploadSuccess={() => void fetchStructure()} />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
