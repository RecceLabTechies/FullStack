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
    <form className="mb-4" role="search">
      <Input
        type="search"
        placeholder="Search staff members..."
        value={search}
        onChange={handleSearch}
        aria-label="Search staff members"
      />
    </form>
  );
}
