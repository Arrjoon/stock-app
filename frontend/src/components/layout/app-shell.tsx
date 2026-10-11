import type { ReactNode } from "react";

import { SiteHeader } from "@/components/layout/site-header";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1 py-8 pb-14">
        <div className="mx-auto w-[min(1080px,94%)]">{children}</div>
      </main>
    </div>
  );
}
