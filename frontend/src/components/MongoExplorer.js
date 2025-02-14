import React, { useState, useEffect } from "react";
import CollectionTable from "./CollectionTable";

function MongoExplorer() {
    const [dbStructure, setDbStructure] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDbStructure();
    }, []);

    const fetchDbStructure = async () => {
        try {
            const response = await fetch("http://localhost:5001/api/db-structure");
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setDbStructure(data);
            setError(null);
        } catch (error) {
            console.error("Error fetching DB structure:", error);
            setError("Failed to fetch database structure");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading database structure...</div>;
    if (error) return <div style={{ color: "red" }}>{error}</div>;

    return (
        <div style={{ padding: "20px" }}>
            <h1>MongoDB Structure Explorer</h1>
            <div
                style={{
                    backgroundColor: "#f5f5f5",
                    padding: "20px",
                    borderRadius: "8px",
                    maxWidth: "1200px",
                    margin: "20px auto",
                }}
            >
                {dbStructure &&
                    Object.entries(dbStructure).map(([dbName, collections]) => (
                        <div key={dbName} style={{ marginBottom: "20px" }}>
                            <h2 style={{ color: "#2196F3" }}>Database: {dbName}</h2>
                            {Object.entries(collections).map(([collName, schema]) => (
                                <div
                                    key={collName}
                                    style={{ marginLeft: "20px", marginBottom: "15px" }}
                                >
                                    <h3 style={{ color: "#4CAF50" }}>Collection: {collName}</h3>
                                    <div style={{ marginLeft: "20px" }}>
                                        <h4>Sample Document:</h4>
                                        <CollectionTable schema={schema} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ))}
            </div>
        </div>
    );
}

export default MongoExplorer;
