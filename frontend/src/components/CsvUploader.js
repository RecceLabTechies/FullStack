import React, { useState } from "react";

function CsvUploader() {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
        setError(null);
        setSuccess(null);
    };

    const handleUpload = async () => {
        if (!file) {
            setError("Please select a file first");
            return;
        }

        if (!file.name.endsWith(".csv")) {
            setError("Please upload a CSV file");
            return;
        }

        setLoading(true);
        setError(null);
        setSuccess(null);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://localhost:5001/api/upload-csv", {
                method: "POST",
                body: formData,
            });

            let data;
            try {
                data = await response.json();
            } catch (e) {
                throw new Error("Failed to parse server response");
            }

            if (!response.ok) {
                throw new Error(data.error || "Upload failed");
            }

            setSuccess(
                `Successfully uploaded ${data.count} records to collection '${data.collection}'`
            );
            setFile(null);
            // Reset the file input
            const fileInput = document.querySelector('input[type="file"]');
            if (fileInput) fileInput.value = "";
        } catch (error) {
            console.error("Upload error:", error);
            setError(error.message || "Failed to upload file");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: "20px" }}>
            <h2>CSV Uploader</h2>
            <div
                style={{
                    backgroundColor: "#f5f5f5",
                    padding: "20px",
                    borderRadius: "8px",
                    maxWidth: "600px",
                    margin: "20px auto",
                }}
            >
                <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    style={{ marginBottom: "20px" }}
                    disabled={loading}
                />
                <button
                    onClick={handleUpload}
                    disabled={!file || loading}
                    style={{
                        padding: "10px 20px",
                        fontSize: "16px",
                        cursor: !file || loading ? "not-allowed" : "pointer",
                        backgroundColor: "#4CAF50",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        marginLeft: "10px",
                    }}
                >
                    {loading ? "Uploading..." : "Upload CSV"}
                </button>

                {error && (
                    <div
                        style={{
                            padding: "10px",
                            backgroundColor: "#ffebee",
                            color: "#c62828",
                            marginTop: "20px",
                            borderRadius: "4px",
                        }}
                    >
                        {error}
                    </div>
                )}

                {success && (
                    <div
                        style={{
                            padding: "10px",
                            backgroundColor: "#e8f5e9",
                            color: "#2e7d32",
                            marginTop: "20px",
                            borderRadius: "4px",
                        }}
                    >
                        {success}
                    </div>
                )}
            </div>
        </div>
    );
}

export default CsvUploader;
