"use client"

import { useState } from "react"
import { Input } from "@/components/ui/input"

export default function SearchBar() {
  const [search, setSearch] = useState("")

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(event.target.value)
    // TODO: Implement search functionality
  }

  return (
    <div className="mb-4">
      <Input type="text" placeholder="Search staff members..." value={search} onChange={handleSearch} />
    </div>
  )
}

