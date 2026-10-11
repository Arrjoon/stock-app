"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { SyncButton } from "@/components/market/sync-button";
import { clearAccessToken } from "@/lib/session";
import { useMe } from "@/lib/use-me";

export function SiteHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const me = useMe();
  const onLogin = pathname === "/" || pathname === "/login";
  const links = onLogin
    ? []
    : [
        { href: "/companies", label: "Watchlist" },
        { href: "/compare", label: "Compare" },
        ...(me?.role === "admin" ? [{ href: "/admin", label: "Admin" }] : []),
      ];

  return (
    <header className="sticky top-0 z-20 border-b border-white/5 bg-[rgba(8,11,18,0.86)] backdrop-blur-md">
      <div className="mx-auto flex min-h-14 w-[min(1180px,94%)] items-center gap-4">
        <Link href={me ? "/companies" : "/"} className="inline-flex items-center gap-2 text-base font-semibold tracking-tight text-ink">
          <span className="size-2 rounded-full bg-[var(--color-up)]" aria-hidden="true" />
          NEPSE
        </Link>
        {me?.role === "admin" && !onLogin ? (
          <div className="ml-auto">
            <SyncButton compact />
          </div>
        ) : null}
        <nav className={`${me?.role === "admin" && !onLogin ? "" : "ml-auto"} flex flex-wrap items-center gap-1 text-sm font-medium text-ink-60`} aria-label="Primary">
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
          {me ? (
            <button
              type="button"
              className="rounded-full px-3 py-1.5 hover:bg-white/5 hover:text-ink"
              onClick={() => {
                clearAccessToken();
                router.push("/");
              }}
            >
              Logout
            </button>
          ) : onLogin ? null : (
            <Link href="/" className="rounded-full px-3 py-1.5 hover:bg-white/5 hover:text-ink">
              Login
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
