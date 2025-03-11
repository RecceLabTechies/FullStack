"use client";

import { NavUser } from "@/components/nav-user";
import {
  Building,
  Clipboard,
  DatabaseBackup,
  LayoutDashboard,
  Settings,
  ShieldEllipsis,
} from "lucide-react";
import { usePathname } from "next/navigation";
import * as React from "react";

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
} from "@/components/ui/sidebar";
import Link from "next/link";

// Types
interface NavigationItem {
  name: string;
  url: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface SidebarConfig {
  currentUser: {
    name: string;
    email: string;
  };
  navigationItems: NavigationItem[];
}

// Memoized configuration
const sidebarConfig: SidebarConfig = {
  currentUser: {
    name: "user",
    email: "user@company.com",
  },
  navigationItems: [
    {
      name: "Home",
      url: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Report",
      url: "/dashboard/report",
      icon: Clipboard,
    },
    {
      name: "Admin",
      url: "/dashboard/admin",
      icon: ShieldEllipsis,
    },
    {
      name: "Settings",
      url: "/dashboard/settings",
      icon: Settings,
    },
    {
      name: "Mongo Manager",
      url: "/dashboard/mongo_manager",
      icon: DatabaseBackup,
    },
  ],
} as const;

// Memoized Navigation Item Component
const NavigationItem: React.FC<{
  item: NavigationItem;
  isActive: boolean;
}> = React.memo(({ item, isActive }) => {
  const Icon = item.icon;

  return (
    <SidebarMenuItem key={item.name}>
      <SidebarMenuButton
        tooltip={item.name}
        className={`transition duration-100 ease-in-out hover:bg-neutral-100 ${
          isActive ? "bg-neutral-100" : ""
        }`}
      >
        <Link
          href={item.url}
          prefetch
          className="flex w-full items-center gap-2"
        >
          <Icon className="size-4" />
          <span>{item.name}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
});
NavigationItem.displayName = "NavigationItem";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <div>
                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <Building className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">COMPANY NAME</span>
                  <span className="">DASHBOARD</span>
                </div>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Platform</SidebarGroupLabel>
          <SidebarMenu>
            {sidebarConfig.navigationItems.map((item) => (
              <NavigationItem
                key={item.name}
                item={item}
                isActive={pathname === item.url}
              />
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={sidebarConfig.currentUser} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
