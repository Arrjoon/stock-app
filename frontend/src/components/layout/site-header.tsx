"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/login", label: "Login" },
  { href: "/companies/nabil", label: "Company" },
  { href: "/compare", label: "Compare" },
  { href: "/admin", label: "Admin" },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-20 border-b border-white/5 bg-[rgba(8,11,18,0.78)] backdrop-blur-md">
      <div className="mx-auto flex min-h-14 w-[min(1080px,94%)] items-center gap-5">
        <Link href="/" className="inline-flex items-center gap-2 text-base font-semibold tracking-tight text-ink">
          <span className="size-2 rounded-full bg-accent" aria-hidden="true" />
          NEPSE
        </Link>
        <nav className="ml-auto flex gap-1 text-sm font-medium text-ink-60" aria-label="Primary">
          {LINKS.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={`rounded-full px-3 py-1.5 hover:bg-white/5 hover:text-ink ${
                  active ? "bg-accent-soft text-ink" : ""
                }`}
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
