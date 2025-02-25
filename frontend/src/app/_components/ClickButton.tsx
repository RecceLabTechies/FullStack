"use client";

import { useState } from "react";

export function ClickButton() {
  const [message, setMessage] = useState<string | null>(null);

  const handleClick = async () => {
    try {
      const response = await fetch("http://localhost:5001/api/click", { method: "POST" });
      const data = await response.json();
      if (response.ok) {
        setMessage("Click recorded! ID: " + data.id);
      } else {
        setMessage("Error: " + data.error);
      }
    } catch (error) {
      setMessage("Failed to connect to the server.");
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={handleClick}
        className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-700"
      >
        Record Click
      </button>
      {message && <p className="text-sm text-white">{message}</p>}
    </div>
  );
}