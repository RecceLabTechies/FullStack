'use client';

/**
 * Staff List Component Module
 * Provides a grid layout of staff member cards with permission management capabilities.
 * Implements real-time permission updates and user-friendly tooltips.
 */
import { useEffect, useState } from 'react';

import { type UserData } from '@/types/types';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

import { usePatchUser } from '@/hooks/use-backend-api';

/**
 * Props interface for the StaffList component
 * @interface StaffListProps
 * @property {UserData[]} users - Array of user data to display
 * @property {() => void} onUsersUpdate - Callback function to trigger user list refresh
 */
interface StaffListProps {
  users: UserData[];
  onUsersUpdate: () => void;
}

/**
 * Main StaffList component that renders a grid of StaffCard components
 * @param {StaffListProps} props - Component props
 * @returns JSX.Element - Grid layout of staff member cards
 */
export default function StaffList({ users, onUsersUpdate }: StaffListProps) {
  return (
    <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" aria-label="Staff members list">
      {users.map((staff) => (
        <StaffCard
          key={staff.username}
          staff={{
            username: staff.username,
            name: staff.username,
            role: staff.role,
            permissions: {
              reportGeneration: staff.report_generation_access,
              chartViewing: staff.chart_access,
              userManagement: staff.user_management_access,
            },
          }}
          onPermissionUpdate={onUsersUpdate}
        />
      ))}
    </section>
  );
}

/**
 * Interface defining the structure of a staff member's data
 * @interface StaffMember
 */
interface StaffMember {
  username: string;
  name: string;
  role: string;
  permissions: {
    userManagement: boolean;
    reportGeneration: boolean;
    chartViewing: boolean;
  };
}

/** Type alias for the permissions object within StaffMember */
type StaffPermissions = StaffMember['permissions'];

/**
 * Props interface for the StaffCard component
 * @interface StaffCardProps
 */
interface StaffCardProps {
  staff: StaffMember;
  onPermissionUpdate: () => void;
}

/**
 * PermissionControls component that handles permission toggles for a staff member
 * Features:
 * - Toggle switches for each permission
 * - Tooltips with permission descriptions
 * - Real-time permission updates
 * - Error handling and success notifications
 *
 * @param {Object} props - Component props
 * @param {StaffPermissions} props.permissions - Current permission states
 * @param {string} props.username - Username of the staff member
 * @param {() => void} props.onPermissionUpdate - Callback for permission updates
 */
function PermissionControls({
  permissions,
  username,
  onPermissionUpdate,
}: {
  permissions: StaffPermissions;
  username: string;
  onPermissionUpdate: () => void;
}) {
  const { patchUser, isLoading } = usePatchUser();

  /**
   * Handles permission toggle changes
   * Maps frontend permission keys to backend API fields
   * @param {keyof StaffPermissions} permission - The permission being toggled
   * @param {boolean} value - The new permission value
   */
  const handlePermissionChange = async (permission: keyof StaffPermissions, value: boolean) => {
    try {
      const permissionMapping = {
        reportGeneration: 'report_generation_access',
        chartViewing: 'chart_access',
        userManagement: 'user_management_access',
      };

      const patchData = {
        [permissionMapping[permission]]: value,
      };

      await patchUser(username, patchData);
      toast.success(`Successfully updated ${permission} permission`);
      onPermissionUpdate(); // Refresh the users list after successful update
    } catch (error) {
      toast.error(
        `Failed to update ${permission} permission: ${error instanceof Error ? error.message : 'Unknown error occurred'}`
      );
    }
  };

  /**
   * Configuration for permission items
   * Defines the display name, description, and current value for each permission
   */
  const permissionItems = [
    {
      name: 'Report Generation',
      description: 'Allow user to generate reports',
      value: permissions.reportGeneration,
      key: 'reportGeneration' as const,
    },
    {
      name: 'Chart Viewing',
      description: 'Allow user to view charts',
      value: permissions.chartViewing,
      key: 'chartViewing' as const,
    },
    {
      name: 'User Management',
      description: 'Allow user to manage other users',
      value: permissions.userManagement,
      key: 'userManagement' as const,
    },
  ];

  return (
    <TooltipProvider>
      <div className="space-y-3">
        {permissionItems.map((item) => (
          <div key={item.name} className="flex items-center justify-between">
            <Tooltip>
              <TooltipTrigger>{item.name}</TooltipTrigger>
              <TooltipContent>
                <p>{item.description}</p>
              </TooltipContent>
            </Tooltip>
            <Switch
              checked={item.value}
              disabled={isLoading}
              onCheckedChange={(checked) => handlePermissionChange(item.key, checked)}
            />
          </div>
        ))}
      </div>
    </TooltipProvider>
  );
}

/**
 * StaffCard component that displays a card for an individual staff member
 * Features:
 * - Displays staff name and role
 * - Contains permission controls
 * - Handles hydration with loading state
 *
 * @param {StaffCardProps} props - Component props
 */
function StaffCard({ staff, onPermissionUpdate }: StaffCardProps) {
  // State to handle hydration mismatch
  const [isMounted, setIsMounted] = useState(false);

  // Effect to set mounted state after hydration
  useEffect(() => {
    setIsMounted(true);
  }, []);

  return (
    <article>
      <Card>
        <CardHeader>
          <CardTitle>{staff.name}</CardTitle>
          <CardDescription>{staff.role}</CardDescription>
        </CardHeader>
        <CardContent>
          <section className="space-y-4">
            {isMounted ? (
              <PermissionControls
                permissions={staff.permissions}
                username={staff.username}
                onPermissionUpdate={onPermissionUpdate}
              />
            ) : (
              <div>Loading permissions...</div>
            )}
          </section>
        </CardContent>
      </Card>
    </article>
  );
}
