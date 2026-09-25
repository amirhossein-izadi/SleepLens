"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MoonStar, Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { Logo } from "@/components/brand/logo";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/studies", label: "Studies", icon: MoonStar },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 flex-col border-r bg-card lg:flex">
      <div className="flex h-16 items-center border-b px-4">
        <Link href="/dashboard">
          <Logo variant="full" />
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-brand-light text-brand" : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
        <Link
          href="/studies?upload=1"
          className="mt-6 flex items-center gap-3 rounded-lg bg-brand-bright px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-primary"
        >
          <Upload className="h-4 w-4" />
          New upload
        </Link>
      </nav>
      <div className="border-t p-4 text-xs text-muted-foreground">
        SleepLens · research tool
      </div>
    </aside>
  );
}

/** Top bar variant for small screens. */
export function MobileNav() {
  const pathname = usePathname();
  return (
    <div className="sticky top-0 z-40 flex h-14 items-center justify-between border-b bg-card px-4 lg:hidden">
      <Link href="/dashboard">
        <Logo variant="full" />
      </Link>
      <nav className="flex items-center gap-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm",
                active ? "bg-brand-light text-brand" : "text-muted-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
