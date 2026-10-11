"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { SyncButton } from "@/components/market/sync-button";
import { useMe } from "@/lib/use-me";

export function SiteHeader() {
  const pathname = usePathname();
  const me = useMe();
  const links = [
    { href: "/companies", label: "Watchlist" },
    { href: "/compare", label: "Compare" },
  ];
  if (me?.role === "admin") {
    links.push({ href: "/admin", label: "Admin" });
  }
  if (!me) {
    links.push({ href: "/login", label: "Login" });
  }

  return (
    <header className="sticky top-0 z-20 border-b border-white/5 bg-[rgba(8,11,18,0.86)] backdrop-blur-md">
      <div className="mx-auto flex min-h-14 w-[min(1180px,94%)] items-center gap-4">
        <Link href="/companies" className="inline-flex items-center gap-2 text-base font-semibold tracking-tight text-ink">
          <span className="size-2 rounded-full bg-[var(--color-up)]" aria-hidden="true" />
          NEPSE
        </Link>
        {me?.role === "admin" ? (
          <div className="ml-auto">
            <SyncButton compact />
          </div>
        ) : null}
        <nav className={`${me?.role === "admin" ? "" : "ml-auto"} flex flex-wrap gap-1 text-sm font-medium text-ink-60`} aria-label="Primary">
          {links.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={`rounded-full px-3 py-1.5 hover:bg-white/5 hover:text-ink ${active ? "bg-accent-soft text-ink" : ""}`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
