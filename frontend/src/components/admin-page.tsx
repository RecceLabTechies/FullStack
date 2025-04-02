/**
 * Admin Page Component Module
 * This module provides the main administrative interface for user management.
 * It implements role-based access control and user management functionality.
 */

'use client';

import { useEffect, useState } from 'react';

import type { UserData } from '@/types/types';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

import { useUsers } from '@/hooks/use-backend-api';

import CreateUserModal from './admin-create-user-modal';
import SearchBar from './admin-search-bar';
import StaffList from './admin-staff-list';

/**
 * Admin Page Component Module
 * This module provides the main administrative interface for user management.
 * It implements role-based access control and user management functionality.
 */

/**
 * Loading skeleton component for the staff list
 * Displays a placeholder grid of cards while the actual data is being fetched
 * @returns JSX.Element representing the loading state
 */
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

/**
 * Main admin page component that provides user management functionality
 * Features:
 * - Role-based access control (Root, Admin, User hierarchy)
 * - User filtering and search
 * - Real-time user list updates
 * - User creation and management
 *
 * @returns JSX.Element representing the admin interface
 */
export default function AdminPage() {
  // State management for user data and filtering
  const [filteredUsers, setFilteredUsers] = useState<UserData[] | null>(null);
  const [currentUser, setCurrentUser] = useState<UserData | null>(null);
  const { data: users, isLoading, error, fetchUsers } = useUsers();

  /**
   * Effect hook to load the current user's data from localStorage
   * This determines the user's permissions and available actions
   */
  useEffect(() => {
    // Get current user from localStorage
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr) as UserData;
      setCurrentUser(user);
    }
  }, []);

  /**
   * Effect hook to fetch all users when the current user is loaded
   * Only fetches data if the current user has appropriate permissions
   */
  useEffect(() => {
    if (currentUser) {
      void fetchUsers();
    }
  }, [currentUser, fetchUsers]);

  /**
   * Effect hook to filter users based on role hierarchy
   * Implements the following rules:
   * - Root users can see all other users
   * - Admin users can only see regular users
   * - Regular users cannot see any other users
   * - Users cannot see themselves in the list
   */
  useEffect(() => {
    if (!users) return;

    // Filter users based on role hierarchy
    const filtered = Array.isArray(users)
      ? users.filter((user) => {
          // Don't show current user
          if (user.email === currentUser?.email) return false;

          // Role hierarchy: root > admin > user
          const currentUserRole = currentUser?.role.toLowerCase() ?? '';
          const userRole = user.role.toLowerCase();

          // If current user is root, they can see all users
          if (currentUserRole === 'root') return true;

          // If current user is admin, they can only see users with role 'user'
          if (currentUserRole === 'admin') {
            return userRole === 'user';
          }

          // If current user is not admin or root, they shouldn't see any users
          return false;
        })
      : [];

    setFilteredUsers(filtered);
  }, [users, currentUser]);

  /**
   * Handles the search functionality for users
   * Filters users based on username and role, while respecting role hierarchy
   * @param searchTerm - The search string to filter users by
   */
  const handleSearch = (searchTerm: string) => {
    if (!users || !Array.isArray(users)) return;

    if (!searchTerm.trim()) {
      setFilteredUsers(
        users.filter((user) => {
          if (user.email === currentUser?.email) return false;
          const currentUserRole = currentUser?.role.toLowerCase() ?? '';
          const userRole = user.role.toLowerCase();
          if (currentUserRole === 'root') return true;
          if (currentUserRole === 'admin') return userRole === 'user';
          return false;
        })
      );
      return;
    }

    const filtered = users.filter(
      (user) =>
        (user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
          user.role.toLowerCase().includes(searchTerm.toLowerCase())) &&
        user.email !== currentUser?.email &&
        (currentUser?.role.toLowerCase() === 'root' ||
          (currentUser?.role.toLowerCase() === 'admin' && user.role.toLowerCase() === 'user'))
    );
    setFilteredUsers(filtered);
  };

  /**
   * Callback function to refresh the users list
   * Called after user creation, deletion, or updates
   */
  const handleUsersUpdate = () => {
    void fetchUsers(); // Refresh the users list
  };

  // Access control check - only allow admin and root users
  if (
    !currentUser ||
    (currentUser.role.toLowerCase() !== 'admin' && currentUser.role.toLowerCase() !== 'root')
  ) {
    return (
      <section className="container mx-auto p-4">
        <Card>
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>You don&apos;t have permission to access this page.</CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  return (
    <section className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Staff Management</CardTitle>
              <CardDescription>Manage your team&apos;s permissions and access</CardDescription>
            </div>
            <CreateUserModal />
          </div>
        </CardHeader>
        <CardContent>
          <SearchBar onSearch={handleSearch} />
          {isLoading ? (
            <SkeletonStaffList />
          ) : error ? (
            <div className="text-destructive" role="alert">
              {error.message}
            </div>
          ) : (
            filteredUsers && <StaffList users={filteredUsers} onUsersUpdate={handleUsersUpdate} />
          )}
        </CardContent>
      </Card>
    </section>
  );
}
