import React from "react";

function CollectionTable({ schema }) {
    // If schema is a string (for empty collections), return early
    if (typeof schema === "string") {
        return <div>{schema}</div>;
    }

    // Handle both single document and array of documents
    const documents = Array.isArray(schema) ? schema : [schema];

    // Get all unique keys from all documents
    const keys = Array.from(new Set(documents.flatMap((doc) => Object.keys(doc))));

    return (
        <div style={{ overflowX: "auto" }}>
            <table
                style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    marginTop: "10px",
                    backgroundColor: "white",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.12)",
                }}
            >
                <thead>
                    <tr>
                        {keys.map((key) => (
                            <th
                                key={key}
                                style={{
                                    padding: "12px",
                                    textAlign: "left",
                                    borderBottom: "2px solid #ddd",
                                    backgroundColor: "#f8f9fa",
                                }}
                            >
                                {key}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {documents.map((doc, index) => (
                        <tr key={index}>
                            {keys.map((key) => (
                                <td
                                    key={key}
                                    style={{
                                        padding: "12px",
                                        borderBottom: "1px solid #ddd",
                                        maxWidth: "300px",
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        whiteSpace: "nowrap",
                                    }}
                                >
                                    {doc[key] === undefined
                                        ? ""
                                        : typeof doc[key] === "object"
                                        ? JSON.stringify(doc[key])
                                        : String(doc[key])}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default CollectionTable;
