'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

import { useRouter } from 'next/navigation';

import * as z from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Bot, Loader2, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';

import { useUsers } from '@/hooks/use-backend-api';

const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address')
    .transform((email) => email.toLowerCase().trim()),
  password: z.string().min(1, 'Password is required').max(100, 'Password is too long'),
});

type LoginValues = z.infer<typeof loginSchema>;

export default function AuthPage() {
  const [error, setError] = useState('');
  const [isNavigating, setIsNavigating] = useState(false);
  const router = useRouter();
  const { data: users, isLoading, fetchUsers } = useUsers();

  useEffect(() => {
    void fetchUsers();
  }, [fetchUsers]);

  const loginForm = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  async function onLoginSubmit(values: LoginValues) {
    try {
      setError('');

      // Regular user check from database
      if (!users) {
        setError('User data is not available. Try again later.');
        toast.error('User data is not available. Try again later.');
        return;
      }

      const user = Array.isArray(users)
        ? users.find((u) => u.email === values.email && u.password === values.password)
        : users.email === values.email && users.password === values.password
          ? users
          : null;

      if (!user) {
        setError('Invalid email or password');
        toast.error('Invalid email or password');
        return;
      }

      // Set both localStorage and cookie
      localStorage.setItem('user', JSON.stringify(user));

      // Set cookie for server-side auth check
      document.cookie = `auth-token=${btoa(JSON.stringify({ username: user.username, email: user.email }))}; path=/; max-age=${60 * 60 * 24 * 7}`; // 7 days expiry

      // Set loading state immediately
      setIsNavigating(true);
      toast.success('Login successful! Redirecting to dashboard...');
      router.push('/dashboard');
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
      setError('An unexpected error occurred during login.');
      toast.error(`Login error: ${errorMessage}`);
      setIsNavigating(false);
    }
  }

  // If we're in the navigating state, show a fullscreen loading overlay
  if (isNavigating) {
    return (
      <div
        className="fixed inset-0 flex flex-col items-center justify-center bg-background"
        role="status"
        aria-live="polite"
      >
        <Loader2 size={48} className="animate-spin text-primary mb-4" aria-hidden="true" />
        <h2 className="text-xl font-medium">Loading your dashboard...</h2>
        <p className="text-muted-foreground mt-2">Please wait while we prepare your experience</p>
      </div>
    );
  }

  return (
    <main className="flex min-h-screen flex-col lg:flex-row">
      {/* Product Information Section */}
      <section
        className="flex flex-1 flex-col justify-center bg-muted/40 p-8 lg:p-12"
        aria-labelledby="product-heading"
      >
        <div className="mx-auto w-full max-w-md space-y-8">
          <header className="space-y-3">
            <h1 id="product-heading" className="text-3xl font-bold tracking-tight sm:text-4xl">
              RecceLabs LLM Dashboard
            </h1>
            <p className="text-lg text-muted-foreground">
              Powerful analytics and AI-driven reports for your marketing needs
            </p>
          </header>

          <div className="space-y-6">
            <article className="flex items-start gap-3">
              <TrendingUp className="mt-1 h-5 w-5 text-primary" aria-hidden="true" />
              <div>
                <h2 className="font-medium">Real-time Analytics</h2>
                <p className="text-sm text-muted-foreground">
                  Monitor marketing performance with interactive dashboards
                </p>
              </div>
            </article>

            <article className="flex items-start gap-3">
              <Bot className="mt-1 h-5 w-5 text-primary" aria-hidden="true" />
              <div>
                <h2 className="font-medium">AI-Powered Reports</h2>
                <p className="text-sm text-muted-foreground">
                  Generate custom reports using natural language queries
                </p>
              </div>
            </article>
          </div>

          <footer className="pt-4">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-muted/40 px-2 text-muted-foreground">Prototype</span>
              </div>
            </div>
          </footer>
        </div>
      </section>

      {/* Auth Form Section */}
      <section
        className="flex flex-1 flex-col justify-center p-8 lg:p-12"
        aria-labelledby="login-heading"
      >
        <div className="mx-auto w-full max-w-sm space-y-6">
          <header className="space-y-2 text-center">
            <h1 id="login-heading" className="text-3xl font-bold">
              Login
            </h1>
            <p className="text-muted-foreground">Enter your email below to login to your account</p>
          </header>
          <Form {...loginForm}>
            <form
              onSubmit={loginForm.handleSubmit(onLoginSubmit)}
              className="space-y-4"
              aria-describedby={error ? 'form-error' : undefined}
            >
              {error && (
                <div
                  className="flex items-center space-x-2 text-destructive"
                  id="form-error"
                  role="alert"
                >
                  <span className="text-sm">{error}</span>
                </div>
              )}
              <FormField
                control={loginForm.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel htmlFor="email">Email</FormLabel>
                    <FormControl>
                      <Input
                        id="email"
                        type="email"
                        placeholder="m@example.com"
                        {...field}
                        aria-describedby="email-error"
                      />
                    </FormControl>
                    <FormMessage id="email-error" />
                  </FormItem>
                )}
              />
              <FormField
                control={loginForm.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel htmlFor="password">Password</FormLabel>
                    <FormControl>
                      <Input
                        id="password"
                        type="password"
                        placeholder="********"
                        {...field}
                        aria-describedby="password-error"
                      />
                    </FormControl>
                    <FormMessage id="password-error" />
                  </FormItem>
                )}
              />
              <Button type="submit" className="w-full" disabled={isLoading} aria-busy={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 size={24} className="mr-2 animate-spin" aria-hidden="true" />
                    Authenticating...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>
          </Form>
        </div>
      </section>
    </main>
  );
}
