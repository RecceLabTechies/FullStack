"use client";

import type { User } from "@/api/dbApi";
import { fetchUsers } from "@/api/dbApi";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Suspense, useEffect, useState } from "react";
import SearchBar from "./SearchBar";
import StaffList from "./StaffList";

export default function AdminPage() {
  const [users, setUsers] = useState<User[] | null>(null);
  const [filteredUsers, setFilteredUsers] = useState<User[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const getUsers = async () => {
      try {
        const fetchedUsers = await fetchUsers();
        setUsers(fetchedUsers);
        setFilteredUsers(fetchedUsers);
      } catch (error) {
        setError("Failed to load users.");
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    void getUsers();
  }, []);

  const handleSearch = (searchTerm: string) => {
    if (!users) return;

    if (!searchTerm.trim()) {
      setFilteredUsers(users);
      return;
    }

    const filtered = users.filter(
      (user) =>
        user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.role.toLowerCase().includes(searchTerm.toLowerCase()),
    );
    setFilteredUsers(filtered);
  };

  return (
    <div className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle>Staff Management</CardTitle>
          <CardDescription>
            Manage your team&apos;s permissions and access
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SearchBar onSearch={handleSearch} />
          <Suspense fallback={<div>Loading staff list...</div>}>
            {loading ? (
              <div>Loading...</div>
            ) : error ? (
              <div>{error}</div>
            ) : (
              filteredUsers && <StaffList users={filteredUsers} />
            )}
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}
