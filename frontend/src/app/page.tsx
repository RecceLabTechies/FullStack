"use client";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { type UserData } from "@/types/types";
import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";
import { Bot, Loader2, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import * as z from "zod";

const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address")
    .transform((email) => email.toLowerCase().trim()),
  password: z
    .string()
    .min(1, "Password is required")
    .min(8, "Password must be at least 8 characters")
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must contain at least one uppercase letter, one lowercase letter, and one number",
    )
    .max(100, "Password is too long"),
});

const signUpSchema = loginSchema
  .extend({
    confirmPassword: z.string(),
    name: z.string().min(1, "Name is required").max(50, "Name is too long"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type LoginValues = z.infer<typeof loginSchema>;
type SignUpValues = z.infer<typeof signUpSchema>;

export default function AuthPage() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [users, setUsers] = useState<UserData[] | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get("http://localhost:5001/api/users");
        setUsers(response.data as UserData[]);
      } catch (error) {
        console.error("Failed to fetch users", error);
        setError("Failed to load user data.");
      }
    };

    void fetchUsers();
  }, []);

  const loginForm = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const signUpForm = useForm<SignUpValues>({
    resolver: zodResolver(signUpSchema),
    defaultValues: {
      email: "",
      password: "",
      confirmPassword: "",
      name: "",
    },
  });

  async function onLoginSubmit(values: LoginValues) {
    try {
      setIsLoading(true);
      setError("");

      // Regular user check from database
      if (!users) {
        setError("User data is not available. Try again later.");
        return;
      }

      const user = users.find(
        (u) => u.email === values.email && u.password === values.password,
      );

      if (!user) {
        setError("Invalid email or password");
        return;
      }

      localStorage.setItem("user", JSON.stringify(user));
      router.push("/dashboard");
    } catch (error) {
      console.error("Login error:", error);
      setError("An unexpected error occurred during login.");
    } finally {
      setIsLoading(false);
    }
  }

  async function onSignUpSubmit(values: SignUpValues) {
    try {
      console.log("Sign up submitted:", values);
    } catch (error) {
      console.error("Sign up error:", error);
    }
  }

  return (
    <main className="flex min-h-screen flex-col lg:flex-row">
      {/* Product Information Section */}
      <section className="flex flex-1 flex-col justify-center bg-muted/40 p-8 lg:p-12">
        <div className="mx-auto w-full max-w-md space-y-8">
          <header className="space-y-3">
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
              RecceLabs LLM Dashboard
            </h1>
            <p className="text-lg text-muted-foreground">
              Powerful analytics and AI-driven reports for your marketing needs
            </p>
          </header>

          <div className="space-y-6">
            <article className="flex items-start gap-3">
              <TrendingUp
                className="mt-1 h-5 w-5 text-primary"
                aria-hidden="true"
              />
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
                <span className="bg-muted/40 px-2 text-muted-foreground">
                  Prototype
                </span>
              </div>
            </div>
          </footer>
        </div>
      </section>

      {/* Auth Form Section */}
      <section className="flex flex-1 flex-col justify-center p-8 lg:p-12">
        <div className="mx-auto w-full max-w-sm space-y-6">
          <header className="space-y-2 text-center">
            <h1 className="text-3xl font-bold">
              {isSignUp ? "Sign Up" : "Login"}
            </h1>
            <p className="text-muted-foreground">
              {isSignUp
                ? "Create a new account to get started"
                : "Enter your email below to login to your account"}
            </p>
          </header>
          {isSignUp ? (
            <Form {...signUpForm}>
              <form
                onSubmit={signUpForm.handleSubmit(onSignUpSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={signUpForm.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel htmlFor="name">Full Name</FormLabel>
                      <FormControl>
                        <Input
                          id="name"
                          placeholder="John Doe"
                          {...field}
                          aria-describedby="name-error"
                        />
                      </FormControl>
                      <FormMessage id="name-error" />
                    </FormItem>
                  )}
                />
                <FormField
                  control={signUpForm.control}
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
                  control={signUpForm.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel htmlFor="password">Password</FormLabel>
                        <span className="text-sm text-muted-foreground">
                          Required
                        </span>
                      </div>
                      <FormControl>
                        <Input
                          id="password"
                          type="password"
                          placeholder="••••••••"
                          {...field}
                          aria-describedby="password-error"
                        />
                      </FormControl>
                      <FormMessage id="password-error" />
                    </FormItem>
                  )}
                />
                <FormField
                  control={signUpForm.control}
                  name="confirmPassword"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel htmlFor="confirmPassword">
                          Confirm Password
                        </FormLabel>
                        <span className="text-sm text-muted-foreground">
                          Required
                        </span>
                      </div>
                      <FormControl>
                        <Input
                          id="confirmPassword"
                          type="password"
                          placeholder="••••••••"
                          {...field}
                          aria-describedby="confirm-password-error"
                        />
                      </FormControl>
                      <FormMessage id="confirm-password-error" />
                    </FormItem>
                  )}
                />
                <Button type="submit" className="w-full">
                  Create Account
                </Button>
              </form>
            </Form>
          ) : (
            <Form {...loginForm}>
              <form
                onSubmit={loginForm.handleSubmit(onLoginSubmit)}
                className="space-y-4"
              >
                {error && (
                  <div className="flex items-center space-x-2 text-red-600">
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
                      <div className="flex items-center justify-between">
                        <FormLabel htmlFor="password">Password</FormLabel>
                        <Link
                          href="/forgot-password"
                          className="text-sm text-muted-foreground underline underline-offset-4 hover:text-primary"
                        >
                          Forgot your password?
                        </Link>
                      </div>
                      <FormControl>
                        <Input
                          id="password"
                          type="password"
                          placeholder="••••••••"
                          {...field}
                          aria-describedby="password-error"
                        />
                      </FormControl>
                      <FormMessage id="password-error" />
                    </FormItem>
                  )}
                />
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    "Sign In"
                  )}
                </Button>
              </form>
            </Form>
          )}
          <footer className="text-center text-sm">
            <small>
              {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
              <button
                onClick={() => setIsSignUp(!isSignUp)}
                className="font-medium text-primary underline underline-offset-4 hover:text-primary/90"
              >
                {isSignUp ? "Sign in" : "Create account"}
              </button>
            </small>
          </footer>
        </div>
      </section>
    </main>
  );
}
