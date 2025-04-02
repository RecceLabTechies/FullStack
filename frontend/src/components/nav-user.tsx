'use client';

/**
 * Navigation User Component Module
 * Provides a user profile dropdown menu in the navigation bar
 * with responsive design for both mobile and desktop views.
 */
import React from 'react';

import { useRouter } from 'next/navigation';

import { ChevronsUpDown, LogOut } from 'lucide-react';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';

/**
 * NavUser component that displays user information and provides logout functionality
 * Features:
 * - User avatar with initials
 * - Dropdown menu with user details
 * - Logout functionality
 * - Responsive design (mobile/desktop)
 * - Accessible dropdown interface
 *
 * @param {Object} props - Component props
 * @param {Object} props.user - User information object
 * @param {string} props.user.name - User's display name
 * @param {string} props.user.email - User's email address
 * @returns JSX.Element - Navigation user interface component
 */
export function NavUser({
  user,
}: {
  user: {
    name: string;
    email: string;
  };
}) {
  const { isMobile } = useSidebar();
  const router = useRouter();
  const userInitials = user.name.slice(0, 2).toUpperCase();

  /**
   * UserAvatar component
   * Displays a circular avatar with user's initials
   * @returns JSX.Element - Avatar component
   */
  const UserAvatar = () => (
    <Avatar className="h-8 w-8 rounded-lg">
      <AvatarFallback className="rounded-lg">{userInitials}</AvatarFallback>
    </Avatar>
  );

  /**
   * UserInfo component
   * Displays user's name and email in a grid layout
   * Features truncation for long text
   * @returns JSX.Element - User information display
   */
  const UserInfo = () => (
    <div className="grid flex-1 text-left text-sm leading-tight">
      <span className="truncate font-semibold">{user.name}</span>
      <span className="truncate text-xs">{user.email}</span>
    </div>
  );

  /**
   * Handles user logout action
   * Clears authentication data and redirects to home page
   */
  const handleLogout = () => {
    // Clear localStorage
    localStorage.removeItem('user');

    // Clear auth cookie by setting expiration to past date
    document.cookie = 'auth-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';

    // Redirect to home/login page
    router.push('/');
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <UserAvatar />
              <UserInfo />
              <ChevronsUpDown className="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
            side={isMobile ? 'bottom' : 'right'}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuLabel className="p-0 font-normal">
              <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                <UserAvatar />
                <UserInfo />
              </div>
            </DropdownMenuLabel>
            <DropdownMenuGroup>
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut />
                <span>Log Out</span>
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
