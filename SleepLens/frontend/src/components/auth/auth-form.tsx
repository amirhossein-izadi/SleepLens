"use client";

/**
 * AuthForm
 * Login / register with client-side validation (react-hook-form + zod) that
 * mirrors the backend envelope errors into field errors.
 */

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AlertCircle, MoonStar } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { extractErrorMessage } from "@/lib/errorUtils";
import { Button, Input } from "@/components/ui";
import { Logo } from "@/components/brand/logo";
import { cn } from "@/lib/utils";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

const registerSchema = z.object({
  full_name: z.string().min(2, "Enter your full name"),
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "At least 8 characters"),
});

type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;

interface AuthFormProps {
  mode: "login" | "register";
}

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const [formError, setFormError] = useState("");

  const loginForm = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const registerForm = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name: "", email: "", password: "" },
  });

  async function onSubmit(values: LoginValues | RegisterValues) {
    setFormError("");
    try {
      const user =
        mode === "register"
          ? await authApi.register({
              email: (values as RegisterValues).email,
              password: (values as RegisterValues).password,
              full_name: (values as RegisterValues).full_name,
            })
          : await authApi.login({
              email: (values as LoginValues).email,
              password: (values as LoginValues).password,
            });
      login(user);
      router.push("/dashboard");
    } catch (err) {
      setFormError(extractErrorMessage(err, "Authentication failed. Please try again."));
    }
  }

  return (
    <div className="w-full max-w-md">
      <Link href="/" className="mb-10 inline-flex items-center gap-3">
        <Logo variant="full" className="h-12" priority />
        <span className="sr-only">SleepLens</span>
      </Link>

      <div className="flex h-9 items-center gap-2 rounded-full border border-border bg-muted/60 px-3 text-xs font-medium text-muted-foreground w-fit">
        {mode === "login" ? "Welcome back" : "Create your account"}
      </div>
      <h1 className="mt-4 text-3xl font-bold tracking-tight">
        {mode === "login" ? "Log in to SleepLens" : "Start decoding sleep"}
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {mode === "register"
          ? "Expert accounts for PSG analysis — staging, sleep depth, confidence and AI reporting."
          : "Your studies, patients and reports are waiting."}
      </p>

      {mode === "login" ? (
        <form onSubmit={loginForm.handleSubmit(onSubmit)} className="mt-8 space-y-4" noValidate>
          <Field label="Email" error={loginForm.formState.errors.email?.message}>
            <Input
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              {...loginForm.register("email")}
              className={cn(loginForm.formState.errors.email && "border-red-400")}
            />
          </Field>
          <Field label="Password" error={loginForm.formState.errors.password?.message}>
            <Input
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
              {...loginForm.register("password")}
              className={cn(loginForm.formState.errors.password && "border-red-400")}
            />
          </Field>
          <SubmitRow formError={formError} loading={loginForm.formState.isSubmitting} label="Log in" />
        </form>
      ) : (
        <form onSubmit={registerForm.handleSubmit(onSubmit)} className="mt-8 space-y-4" noValidate>
          <Field label="Full name" error={registerForm.formState.errors.full_name?.message}>
            <Input
              placeholder="Jane Doe"
              autoComplete="name"
              {...registerForm.register("full_name")}
              className={cn(registerForm.formState.errors.full_name && "border-red-400")}
            />
          </Field>
          <Field label="Email" error={registerForm.formState.errors.email?.message}>
            <Input
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              {...registerForm.register("email")}
              className={cn(registerForm.formState.errors.email && "border-red-400")}
            />
          </Field>
          <Field label="Password" error={registerForm.formState.errors.password?.message}>
            <Input
              type="password"
              placeholder="At least 8 characters"
              autoComplete="new-password"
              {...registerForm.register("password")}
              className={cn(registerForm.formState.errors.password && "border-red-400")}
            />
          </Field>
          <SubmitRow formError={formError} loading={registerForm.formState.isSubmitting} label="Create account" />
        </form>
      )}

      {mode === "login" && (
        <div className="mt-6 rounded-lg border border-dashed bg-muted/30 px-4 py-3 text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Demo account:</span>{" "}
          demo@sleeplens.local · demopass123
        </div>
      )}

      <p className="mt-6 text-center text-sm text-muted-foreground">
        {mode === "register" ? (
          <>
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-brand-bright hover:underline">
              Log in
            </Link>
          </>
        ) : (
          <>
            New to SleepLens?{" "}
            <Link href="/register" className="font-medium text-brand-bright hover:underline">
              Create an account
            </Link>
          </>
        )}
      </p>

      <div className="mt-10 flex items-center gap-2 text-xs text-muted-foreground">
        <MoonStar className="h-3.5 w-3.5" />
        Sleep stage classification · Sleep depth · AI reporting
      </div>
    </div>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{label}</label>
      {children}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

function SubmitRow({
  formError,
  loading,
  label,
}: {
  formError: string;
  loading: boolean;
  label: string;
}) {
  return (
    <div className="space-y-3 pt-2">
      {formError && (
        <p className="flex items-start gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {formError}
        </p>
      )}
      <Button type="submit" variant="bright" className="w-full" loading={loading}>
        {label}
      </Button>
    </div>
  );
}
