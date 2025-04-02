/**
 * Dashboard Layout Component Module
 * Provides the main layout structure for the dashboard interface,
 * including sidebar, breadcrumb navigation, and content area.
 */

'use client';

import React from 'react';

import { usePathname } from 'next/navigation';

import { AppSidebar } from '@/components/app-sidebar';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Separator } from '@/components/ui/separator';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';

/**
 * Dashboard Layout Component Module
 * Provides the main layout structure for the dashboard interface,
 * including sidebar, breadcrumb navigation, and content area.
 */

/**
 * Generates breadcrumb items from the current pathname
 * Features:
 * - Splits pathname into segments
 * - Capitalizes first letter of each segment
 * - Generates appropriate href for each segment
 * - Marks the last item for special rendering
 *
 * @param {string} pathname - Current URL pathname
 * @returns Array of breadcrumb items with href, label, and isLast properties
 */
const getBreadcrumbItems = (pathname: string) =>
  pathname
    .split('/')
    .filter(Boolean)
    .map((segment, index, segments) => ({
      href: `/${segments.slice(0, index + 1).join('/')}`,
      label: segment.charAt(0).toUpperCase() + segment.slice(1),
      isLast: index === segments.length - 1,
    }));

/**
 * Main dashboard layout component that wraps all dashboard pages
 * Features:
 * - Responsive sidebar with collapse functionality
 * - Dynamic breadcrumb navigation
 * - Consistent header layout
 * - Main content area
 *
 * Layout Structure:
 * - SidebarProvider: Manages sidebar state
 *   - AppSidebar: Main navigation sidebar
 *   - SidebarInset: Main content area
 *     - Header: Contains sidebar trigger and breadcrumbs
 *     - Main: Renders child components
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components to render in the layout
 * @returns JSX.Element - Dashboard layout structure
 */
export function DashboardLayoutContent({ children }: { children: React.ReactNode }) {
  const breadcrumbItems = getBreadcrumbItems(usePathname());

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="bg-sidebar-background">
        <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
          <nav className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                {breadcrumbItems.map((item, index) => (
                  <React.Fragment key={item.href}>
                    <BreadcrumbItem>
                      {item.isLast ? (
                        <BreadcrumbPage>{item.label}</BreadcrumbPage>
                      ) : (
                        <BreadcrumbLink href={item.href}>{item.label}</BreadcrumbLink>
                      )}
                    </BreadcrumbItem>
                    {index < breadcrumbItems.length - 1 && <BreadcrumbSeparator />}
                  </React.Fragment>
                ))}
              </BreadcrumbList>
            </Breadcrumb>
          </nav>
        </header>
        <main>{children}</main>
      </SidebarInset>
    </SidebarProvider>
  );
}
