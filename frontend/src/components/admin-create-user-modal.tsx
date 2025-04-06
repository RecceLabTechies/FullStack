/**
 * Create User Modal Component Module
 * Provides a modal interface for creating new users with role-based permissions
 * and detailed form validation.
 */
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import * as z from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { PlusCircle } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';

import { useAddUser } from '@/hooks/use-backend-api';

/**
 * Zod schema for user creation form validation
 * Defines the structure and validation rules for new user data:
 * - Username: Required
 * - Email: Required, must be valid email format
 * - Password: Required, min 8 chars, must contain uppercase, lowercase, and number
 * - Role: Must be one of 'user', 'admin', or 'root'
 * - Various boolean flags for specific access permissions
 * - Company: Required field for organizational assignment
 */
const formSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address')
    .transform((email) => email.toLowerCase().trim()),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters')
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      'Password must contain at least one uppercase letter, one lowercase letter, and one number'
    )
    .max(100, 'Password is too long'),
  role: z.enum(['user', 'admin', 'root']),
  report_generation_access: z.boolean(),
  chart_access: z.boolean(),
  user_management_access: z.boolean(),
  company: z.string().min(1, 'Company is required'),
});

/**
 * CreateUserModal Component
 * A modal dialog component that provides a form interface for creating new users.
 * Features:
 * - Form validation using Zod schema
 * - Role selection (user, admin, root)
 * - Granular permission controls
 * - Success/error notifications
 * - Automatic form reset after successful submission
 *
 * @returns JSX.Element - The modal dialog component
 */
export default function CreateUserModal() {
  // State for controlling modal visibility
  const [open, setOpen] = useState(false);
  const { addUser, isLoading } = useAddUser();

  /**
   * Form initialization with react-hook-form
   * Sets up validation and default values for all fields
   */
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      role: 'user',
      report_generation_access: false,
      chart_access: false,
      user_management_access: false,
      company: 'default',
    },
  });

  /**
   * Form submission handler
   * Processes the form data, creates the user, and handles success/error states
   * @param values - The validated form data matching the formSchema type
   */
  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      await addUser(values);
      toast.success('User created successfully');
      setOpen(false);
      form.reset();
    } catch (err) {
      toast.error(
        `Failed to create user: ${err instanceof Error ? err.message : 'Unknown error occurred'}`
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default" size="sm">
          <PlusCircle className="mr-2 h-4 w-4" />
          New User
        </Button>
      </DialogTrigger>
      <DialogContent className="flex max-h-[90vh] flex-col overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New User</DialogTitle>
          <DialogDescription>
            Enter user details below to create a new account with appropriate permissions.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel htmlFor="username">Username</FormLabel>
                  <FormControl>
                    <Input id="username" {...field} aria-describedby="username-description" />
                  </FormControl>
                  <FormDescription id="username-description">
                    This will be their display name in the system.
                  </FormDescription>
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
                    <Input type="email" placeholder="john.doe@example.com" {...field} />
                  </FormControl>
                  <FormDescription>
                    The email address will be used for login and communications.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input type="password" {...field} placeholder="••••••••" />
                  </FormControl>
                  <FormDescription>
                    Password must be at least 8 characters and contain at least one uppercase
                    letter, one lowercase letter, and one number.
                  </FormDescription>
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
                    <Input {...field} placeholder="Company name" />
                  </FormControl>
                  <FormDescription>The company this user belongs to.</FormDescription>
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
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a role" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="user">User</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="root">Root</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    User: Basic access | Admin: Advanced access | Root: Full system access
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="report_generation_access"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel>Report Generation</FormLabel>
                    <FormDescription>Allow user to generate and export reports</FormDescription>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="chart_access"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel>Chart Access</FormLabel>
                    <FormDescription>Allow user to view and interact with charts</FormDescription>
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
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel>User Management</FormLabel>
                    <FormDescription>
                      Allow user to manage other users and their permissions
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Creating...' : 'Create User'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
