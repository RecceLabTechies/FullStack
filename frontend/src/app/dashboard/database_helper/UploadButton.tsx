"use client";

import { useState } from "react";

export function UploadButton() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0] ?? null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus("Please select a CSV file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://localhost:5001/api/upload-csv", {
        method: "POST",
        body: formData,
        headers: {
          Accept: "application/json",
        },
      });

      const result = await response.json();

      if (response.ok) {
        setUploadStatus(
          `Success: Uploaded ${result.count} records to ${result.collection}`,
        );
      } else {
        setUploadStatus(`Error: ${result.error}`);
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      setUploadStatus("Error uploading file.");
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <input
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        className="text-white"
      />
      <button
        onClick={handleUpload}
        className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-700"
      >
        Upload CSV
      </button>
      {uploadStatus && <p className="text-sm text-white">{uploadStatus}</p>}
    </div>
  );
}
