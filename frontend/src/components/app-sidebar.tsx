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

const sidebarConfig = {
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
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
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
              <SidebarMenuItem key={item.name}>
                <SidebarMenuButton
                  tooltip={item.name}
                  className="transition duration-100 ease-in-out hover:bg-neutral-100"
                >
                  {item.icon && (
                    <Link href={item.url}>
                      <item.icon className="size-4" />
                    </Link>
                  )}
                  <Link href={item.url}>
                    <span>{item.name}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
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
