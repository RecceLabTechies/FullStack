'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

import * as z from 'zod';
import { type UserData } from '@/types/types';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';

import { useUpdateUser } from '@/hooks/use-backend-api';

const settingsFormSchema = z
  .object({
    username: z.string().min(2, {
      message: 'Username must be at least 2 characters.',
    }),
    email: z.string().email({
      message: 'Please enter a valid email address.',
    }),
    company: z.string().min(1, {
      message: 'Company name is required.',
    }),
    role: z.string(),
    chart_access: z.boolean(),
    report_generation_access: z.boolean(),
    user_management_access: z.boolean(),
    currentPassword: z.string().optional(),
    newPassword: z
      .string()
      .optional()
      .transform((val) => (val === '' ? undefined : val))
      .refine((val) => val === undefined || val.length >= 6, {
        message: 'New password must be at least 6 characters.',
      }),
    confirmNewPassword: z.string().optional(),
  })
  .refine(
    (data) => {
      // Only validate if user is trying to change password
      if (!data.newPassword) {
        return true;
      }
      // Require current password if trying to set new password
      if (!data.currentPassword && data.newPassword) {
        return false;
      }
      return true;
    },
    {
      message: 'Current password is required to change password',
      path: ['currentPassword'],
    }
  )
  .refine(
    (data) => {
      // Only validate if user is trying to change password
      if (!data.newPassword) {
        return true;
      }
      return data.newPassword === data.confirmNewPassword;
    },
    {
      message: 'Passwords do not match',
      path: ['confirmNewPassword'],
    }
  );

type SettingsFormValues = z.infer<typeof settingsFormSchema>;

const defaultValues: Partial<SettingsFormValues> = {
  username: '',
  email: '',
  company: '',
  role: '',
  chart_access: false,
  report_generation_access: false,
  user_management_access: false,
  currentPassword: '',
  newPassword: '',
  confirmNewPassword: '',
};

export default function SettingsPage() {
  const [originalUser, setOriginalUser] = useState<UserData | null>(null);
  const { updateUser, isLoading, error } = useUpdateUser();

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsFormSchema),
    defaultValues,
  });

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr) as UserData;
      setOriginalUser(user);
      form.reset({
        username: user.username,
        email: user.email,
        company: user.company,
        role: user.role,
        chart_access: user.chart_access,
        report_generation_access: user.report_generation_access,
        user_management_access: user.user_management_access,
        currentPassword: user.password,
        newPassword: '',
        confirmNewPassword: '',
      });
    }
  }, [form]);

  async function onSubmit(data: SettingsFormValues) {
    if (!originalUser) {
      toast.error('User data not found');
      return;
    }

    try {
      // Prepare user data for update
      const userData: UserData = {
        ...originalUser,
        username: data.username,
        email: data.email,
        company: data.company,
        role: data.role,
        chart_access: data.chart_access,
        report_generation_access: data.report_generation_access,
        user_management_access: data.user_management_access,
      };

      // Add password if it's being changed
      if (data.newPassword) {
        // Verify current password
        if (data.currentPassword !== originalUser.password) {
          toast.error('Current password is incorrect');
          return;
        }
        userData.password = data.newPassword;
      }

      // Update user in database
      await updateUser(originalUser.username, userData);

      // Update localStorage with new user data
      localStorage.setItem('user', JSON.stringify(userData));

      // Update original user state
      setOriginalUser(userData);

      // Reset password fields
      form.setValue('currentPassword', userData.password);
      form.setValue('newPassword', '');
      form.setValue('confirmNewPassword', '');

      toast.success('Settings updated successfully');
    } catch (err) {
      toast.error('Failed to update settings');
      console.error(err);
    }
  }

  return (
    <main className="container mx-auto max-w-2xl space-y-6 p-4 pb-16">
      <header className="space-y-0.5">
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your account settings and permissions.</p>
      </header>
      <Separator className="my-6" />

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          Error: {error.message}
        </div>
      )}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          {/* General Settings */}
          <section className="space-y-6">
            <h2 className="text-lg font-medium">General</h2>
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Username</FormLabel>
                  <FormControl>
                    <Input placeholder="Your username" {...field} />
                  </FormControl>
                  <FormDescription>This is your display username.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input placeholder="Your email" {...field} />
                  </FormControl>
                  <FormDescription>Your registered email address.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="company"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Company</FormLabel>
                  <FormControl>
                    <Input placeholder="Your company" {...field} />
                  </FormControl>
                  <FormDescription>The company you represent.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <FormControl>
                    <Input placeholder="Your role" {...field} disabled />
                  </FormControl>
                  <FormDescription>Your current role in the system.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </section>

          <Separator />

          {/* Password Change */}
          <section className="space-y-6">
            <h2 className="text-lg font-medium">Change Password</h2>
            <FormField
              control={form.control}
              name="currentPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Current Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="Current password" {...field} />
                  </FormControl>
                  <FormDescription>Enter your current password to verify.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="newPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>New Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="New password" {...field} />
                  </FormControl>
                  <FormDescription>Enter your new password.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="confirmNewPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm New Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="Confirm new password" {...field} />
                  </FormControl>
                  <FormDescription>Confirm your new password.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </section>

          <Separator />

          {/* Access Permissions */}
          <section className="space-y-6">
            <h2 className="text-lg font-medium">Access Permissions</h2>
            <div className="space-y-4">
              <FormField
                control={form.control}
                name="chart_access"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Chart Access</FormLabel>
                      <FormDescription>Access to view and analyze charts</FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="report_generation_access"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Report Generation</FormLabel>
                      <FormDescription>Access to generate reports</FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="user_management_access"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">User Management</FormLabel>
                      <FormDescription>Access to manage users</FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>
          </section>

          <Button type="submit" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 size={16} className="mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </form>
      </Form>
    </main>
  );
}
