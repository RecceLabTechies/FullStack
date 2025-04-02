/**
 * Search Bar Component Module
 * Provides a real-time search input for filtering staff members
 * in the admin interface. Implements controlled input with immediate search feedback.
 */

'use client';

import { useState } from 'react';

import { Input } from '@/components/ui/input';

/**
 * Search Bar Component Module
 * Provides a real-time search input for filtering staff members
 * in the admin interface. Implements controlled input with immediate search feedback.
 */

/**
 * Props interface for the SearchBar component
 * @interface SearchBarProps
 * @property {(searchTerm: string) => void} onSearch - Callback function that receives the current search term
 */
interface SearchBarProps {
  onSearch: (searchTerm: string) => void;
}

/**
 * SearchBar component that provides real-time search functionality
 * Features:
 * - Controlled input component
 * - Real-time search updates
 * - Accessible search input with proper ARIA labels
 * - Debounced search callback (handled by parent)
 *
 * @param {SearchBarProps} props - Component props
 * @returns JSX.Element - Search form with input field
 */
export default function SearchBar({ onSearch }: SearchBarProps) {
  // State to track the current search term
  const [search, setSearch] = useState('');

  /**
   * Handles changes to the search input
   * Updates local state and triggers the search callback
   * @param {React.ChangeEvent<HTMLInputElement>} event - Input change event
   */
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
