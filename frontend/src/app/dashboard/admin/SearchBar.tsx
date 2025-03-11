"use client";

import { Input } from "@/components/ui/input";
import { useState } from "react";

interface SearchBarProps {
  onSearch: (searchTerm: string) => void;
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [search, setSearch] = useState("");

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    const searchTerm = event.target.value;
    setSearch(searchTerm);
    onSearch(searchTerm);
  };

  return (
    <div className="mb-4">
      <Input
        type="text"
        placeholder="Search staff members..."
        value={search}
        onChange={handleSearch}
      />
    </div>
  );
}
