"use client";

import { AuthGuard } from "./components/guards";
import { Sidebar, MobileNav, UserMenu } from "./components/layout";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-dvh">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col lg:ml-60">
          <MobileNav />
          <header className="hidden h-16 items-center justify-between border-b bg-card/60 px-8 lg:flex">
            <div />
            <UserMenu />
          </header>
          <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>
    </AuthGuard>
  );
}
