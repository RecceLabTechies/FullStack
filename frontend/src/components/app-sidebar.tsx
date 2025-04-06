'use client';

import * as React from 'react';
import { useEffect, useState } from 'react';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { type UserData } from '@/types/types';
import { Building, Clipboard, LayoutDashboard, Settings, ShieldEllipsis } from 'lucide-react';

import { NavUser } from '@/components/nav-user';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar';

// Navigation items configuration with permission requirements
const navigationItems = [
  {
    name: 'Home',
    url: '/dashboard',
    icon: LayoutDashboard,
    requiresPermission: false,
  },
  {
    name: 'Report',
    url: '/dashboard/report',
    icon: Clipboard,
    requiresPermission: true,
    permission: 'report_generation_access',
  },
  {
    name: 'Admin',
    url: '/dashboard/admin',
    icon: ShieldEllipsis,
    requiresPermission: true,
    permission: 'user_management_access',
  },
  {
    name: 'Settings',
    url: '/dashboard/settings',
    icon: Settings,
    requiresPermission: false,
  },
] as const;

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname();
  const [user, setUser] = useState<UserData | null>(null);

  useEffect(() => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) setUser(JSON.parse(userStr) as UserData);
    } catch (error) {
      console.error('Error parsing user data:', error);
    }
  }, []);

  // Filter navigation items based on user permissions
  const authorizedNavItems = navigationItems.filter((item) => {
    if (!item.requiresPermission) return true;
    if (!user) return false;
    return item.permission ? user[item.permission as keyof UserData] : true;
  });

  return (
    <Sidebar
      collapsible="icon"
      className="bg-sidebar-background text-sidebar-foreground"
      {...props}
    >
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <div>
                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <Building className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">{user?.company ?? 'COMPANY NAME'}</span>
                </div>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-sidebar-foreground">Platform</SidebarGroupLabel>
          <SidebarMenu>
            {authorizedNavItems.map((item) => (
              <SidebarMenuItem key={item.name}>
                <SidebarMenuButton
                  tooltip={item.name}
                  className={`hover:bg-sidebar-accent transition duration-100 ease-in-out ${
                    pathname === item.url ? 'bg-sidebar-accent' : ''
                  }`}
                  asChild
                >
                  <Link href={item.url} prefetch className="flex w-full items-center gap-2">
                    <item.icon className="size-4" />
                    <span>{item.name}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <NavUser
          user={
            user
              ? { name: user.username, email: user.email }
              : { name: 'Guest', email: 'guest@example.com' }
          }
        />
      </SidebarFooter>
      <SidebarRail className="border-sidebar-border" />
    </Sidebar>
  );
}
