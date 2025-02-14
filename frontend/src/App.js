import React, { useState, useEffect } from "react";
import MongoExplorer from "./components/MongoExplorer";

function App() {
    const [clicks, setClicks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showExplorer, setShowExplorer] = useState(false);

    const fetchClicks = async () => {
        try {
            const response = await fetch("http://localhost:5001/api/clicks");
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setClicks(data);
            setError(null);
        } catch (error) {
            console.error("Error fetching clicks:", error);
            setError("Failed to fetch clicks. Please try again later.");
        }
    };

    useEffect(() => {
        fetchClicks();
        // Set up polling every 5 seconds
        const interval = setInterval(fetchClicks, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleClick = async () => {
        setLoading(true);
        try {
            const response = await fetch("http://localhost:5001/api/click", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            await fetchClicks();
            setError(null);
        } catch (error) {
            console.error("Error recording click:", error);
            setError("Failed to record click. Please try again later.");
        }
        setLoading(false);
    };

    return (
        <div style={{ padding: "20px" }}>
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "20px",
                }}
            >
                <h1>MongoDB Click Counter</h1>
                <button
                    onClick={() => setShowExplorer(!showExplorer)}
                    style={{
                        padding: "10px 20px",
                        fontSize: "16px",
                        cursor: "pointer",
                        backgroundColor: "#2196F3",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                    }}
                >
                    {showExplorer ? "Hide DB Structure" : "Show DB Structure"}
                </button>
            </div>

            {showExplorer ? (
                <MongoExplorer />
            ) : (
                <div>
                    {error && (
                        <div
                            style={{
                                padding: "10px",
                                backgroundColor: "#ffebee",
                                color: "#c62828",
                                marginBottom: "20px",
                                borderRadius: "4px",
                            }}
                        >
                            {error}
                        </div>
                    )}

                    <button
                        onClick={handleClick}
                        disabled={loading}
                        style={{
                            padding: "10px 20px",
                            fontSize: "16px",
                            margin: "20px 0",
                            cursor: loading ? "not-allowed" : "pointer",
                            backgroundColor: "#4CAF50",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                        }}
                    >
                        {loading ? "Recording..." : "Click Me!"}
                    </button>

                    <h2>Click History:</h2>
                    <div style={{ maxHeight: "400px", overflowY: "auto" }}>
                        {clicks.length === 0 ? (
                            <p>No clicks recorded yet.</p>
                        ) : (
                            clicks.map((click) => (
                                <div
                                    key={click._id}
                                    style={{
                                        padding: "10px",
                                        margin: "5px 0",
                                        backgroundColor: "#f5f5f5",
                                        borderRadius: "4px",
                                        boxShadow: "0 1px 3px rgba(0,0,0,0.12)",
                                    }}
                                >
                                    <p>Time: {new Date(click.timestamp).toLocaleString()}</p>
                                    <p>Message: {click.message}</p>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;
