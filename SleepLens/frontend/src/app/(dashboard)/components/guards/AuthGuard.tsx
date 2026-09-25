"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { useMeQuery } from "@/lib/api/queries";
import { LoadingSpinner } from "@/components/ui";

/**
 * Client-side auth guard: redirects to /login when the persisted session is
 * absent, or the /accounts/me/ probe comes back unauthorized.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const hasHydrated = useAuthStore((state) => state._hasHydrated);
  const meQuery = useMeQuery(hasHydrated && isAuthenticated);

  useEffect(() => {
    if (!hasHydrated) return;
    if (!isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [hasHydrated, isAuthenticated, pathname, router]);

  useEffect(() => {
    if (meQuery.isError) {
      useAuthStore.getState().logout();
      router.replace("/login");
    }
  }, [meQuery.isError, router]);

  if (!hasHydrated || !isAuthenticated || meQuery.isLoading) {
    return <LoadingSpinner text="Checking your session…" className="min-h-dvh" />;
  }
  return <>{children}</>;
}
