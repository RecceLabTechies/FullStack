"use client";

import { fetchDbStructure, uploadCsv } from "@/api/backendApi";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { type DbStructure } from "@/types/types";
import React, { useCallback, useState } from "react";

interface UploadButtonProps {
  onUploadSuccess?: () => void;
}

// Define a type for collection documents
type CollectionDocument = Record<string, unknown>;

const LoadingSpinner = () => (
  <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-current" />
);

const StatusMessage = ({
  message,
  type,
}: {
  message: string;
  type: "success" | "error" | "info";
}) => {
  const styles = {
    success: "bg-primary/10 text-primary",
    error: "bg-destructive/15 text-destructive",
    info: "text-muted-foreground",
  };

  return <div className={`rounded-md p-3 ${styles[type]}`}>{message}</div>;
};

const CollectionTable = React.memo(
  ({ collection }: { collection: CollectionDocument[] }) => {
    if (!collection.length) return null;

    const headers = Object.keys(collection[0] ?? {});

    return (
      <div className="rounded-lg border">
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
                  <TableCell key={key}>
                    {typeof value === "object" && value !== null
                      ? JSON.stringify(value)
                      : String(value)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  },
);

CollectionTable.displayName = "CollectionTable";

const DatabaseStructure = React.memo(
  ({ dbStructure }: { dbStructure: DbStructure }) => {
    return (
      <div className="mt-6 space-y-6">
        {Object.entries(dbStructure).map(([dbName, collections]) => (
          <Card key={dbName}>
            <CardHeader>
              <CardTitle className="text-xl">{dbName}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(
                  collections as Record<string, CollectionDocument[] | string>,
                ).map(([collectionName, collection]) => (
                  <div key={collectionName} className="space-y-2">
                    <h3 className="text-lg font-semibold">
                      Collection: {collectionName}
                    </h3>
                    {typeof collection === "string" ? (
                      <p className="text-muted-foreground">{collection}</p>
                    ) : Array.isArray(collection) && collection.length > 0 ? (
                      <CollectionTable collection={collection} />
                    ) : (
                      <p className="text-muted-foreground">No data available</p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  },
);

DatabaseStructure.displayName = "DatabaseStructure";

function UploadButton({ onUploadSuccess }: UploadButtonProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0] ?? null;
      setSelectedFile(file);
      setUploadStatus(null);
    },
    [],
  );

  const handleUpload = useCallback(async () => {
    if (!selectedFile) {
      setUploadStatus("Please select a CSV file.");
      return;
    }

    if (!selectedFile.name.endsWith(".csv")) {
      setUploadStatus("Only CSV files are accepted.");
      return;
    }

    setIsUploading(true);
    setUploadStatus("Uploading...");

    try {
      const result = await uploadCsv(selectedFile);

      if (result) {
        setUploadStatus(
          `Success: Uploaded ${result.count} records to ${result.collection}`,
        );
        setSelectedFile(null);
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput instanceof HTMLInputElement) {
          fileInput.value = "";
        }
        onUploadSuccess?.();
      } else {
        setUploadStatus("Error: Failed to upload CSV");
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      setUploadStatus(
        `Error uploading file: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setIsUploading(false);
    }
  }, [selectedFile, onUploadSuccess]);

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
            <LoadingSpinner />
            <span className="ml-2">Uploading...</span>
          </>
        ) : (
          "Upload CSV"
        )}
      </Button>
      {uploadStatus && (
        <StatusMessage
          message={uploadStatus}
          type={uploadStatus.startsWith("Success") ? "success" : "error"}
        />
      )}
    </div>
  );
}

export default function DatabaseHelper() {
  const [dbStructure, setDbStructure] = useState<DbStructure | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDbStructure = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchDbStructure();
      if (data) {
        setDbStructure(data);
      } else {
        setError("Failed to fetch database structure");
      }
    } catch (err) {
      setError(
        `Error fetching database structure: ${err instanceof Error ? err.message : String(err)}`,
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadDbStructure();
  }, [loadDbStructure]);

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
            <section className="space-y-4">
              {isLoading && (
                <div className="flex items-center space-x-4">
                  <LoadingSpinner />
                  <p className="text-muted-foreground">
                    Loading database structure...
                  </p>
                </div>
              )}
              {error && <StatusMessage message={error} type="error" />}
              {dbStructure && (
                <StatusMessage
                  message="Database structure loaded successfully!"
                  type="success"
                />
              )}
              {dbStructure && <DatabaseStructure dbStructure={dbStructure} />}
            </section>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
            <CardDescription>
              Refresh the database structure or upload new data.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={() => void loadDbStructure()}
              disabled={isLoading}
              variant="secondary"
              className="w-full sm:w-auto"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner />
                  <span className="ml-2">Refreshing...</span>
                </>
              ) : (
                "Refresh Database Structure"
              )}
            </Button>
            <UploadButton onUploadSuccess={() => void loadDbStructure()} />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
