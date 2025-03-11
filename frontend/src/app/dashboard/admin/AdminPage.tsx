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
import { Skeleton } from "@/components/ui/skeleton";
import { useEffect, useState } from "react";
import SearchBar from "./SearchBar";
import StaffList from "./StaffList";

function SkeletonStaffList() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <Card key={index}>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-24" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-6 w-10" />
                </div>
              ))}
            </div>
          </CardContent>
          <div className="p-6 pt-0">
            <Skeleton className="h-10 w-28" />
          </div>
        </Card>
      ))}
    </div>
  );
}

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
          {loading ? (
            <SkeletonStaffList />
          ) : error ? (
            <div className="text-destructive">{error}</div>
          ) : (
            filteredUsers && <StaffList users={filteredUsers} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
