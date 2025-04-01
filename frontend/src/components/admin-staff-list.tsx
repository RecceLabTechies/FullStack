'use client';

import { useEffect, useState } from 'react';

import { type UserData } from '@/types/types';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

import { usePatchUser } from '@/hooks/use-backend-api';

interface StaffListProps {
  users: UserData[];
  onUsersUpdate: () => void;
}

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

type StaffPermissions = StaffMember['permissions'];

interface StaffCardProps {
  staff: StaffMember;
  onPermissionUpdate: () => void;
}

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

function StaffCard({ staff, onPermissionUpdate }: StaffCardProps) {
  const [isMounted, setIsMounted] = useState(false);

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
