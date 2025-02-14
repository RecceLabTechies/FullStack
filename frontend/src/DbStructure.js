import React, { useState, useEffect } from "react";

function DbStructure() {
    const [structure, setStructure] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStructure();
    }, []);

    const fetchStructure = async () => {
        try {
            const response = await fetch("http://localhost:5001/api/db-structure");
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setStructure(data);
            setError(null);
        } catch (error) {
            console.error("Error fetching database structure:", error);
            setError("Failed to fetch database structure. Please try again later.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading database structure...</div>;
    if (error) return <div style={{ color: "red" }}>{error}</div>;
    if (!structure) return <div>No database structure available.</div>;

    return (
        <div style={{ padding: "20px" }}>
            <h1>MongoDB Database Structure</h1>
            {Object.entries(structure).map(([collectionName, collectionData]) => (
                <div
                    key={collectionName}
                    style={{
                        marginBottom: "30px",
                        padding: "20px",
                        backgroundColor: "#f5f5f5",
                        borderRadius: "8px",
                        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    }}
                >
                    <h2 style={{ color: "#2196F3" }}>{collectionName}</h2>
                    <p>
                        <strong>Document Count:</strong> {collectionData.document_count}
                    </p>

                    <div style={{ marginTop: "15px" }}>
                        <h3>Fields:</h3>
                        <ul style={{ listStyle: "none", padding: 0 }}>
                            {collectionData.fields.map((field) => (
                                <li
                                    key={field}
                                    style={{
                                        padding: "5px 10px",
                                        margin: "5px 0",
                                        backgroundColor: "#e3f2fd",
                                        borderRadius: "4px",
                                    }}
                                >
                                    {field}
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div style={{ marginTop: "15px" }}>
                        <h3>Sample Document:</h3>
                        <pre
                            style={{
                                backgroundColor: "#fff",
                                padding: "15px",
                                borderRadius: "4px",
                                overflow: "auto",
                            }}
                        >
                            {JSON.stringify(collectionData.sample_document, null, 2)}
                        </pre>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default DbStructure;
