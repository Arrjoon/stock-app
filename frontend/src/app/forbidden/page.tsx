import Link from "next/link";

export default function ForbiddenPage() {
  return (
    <div className="grid max-w-lg gap-3">
      <p className="text-sm uppercase tracking-wide text-[var(--color-down)]">403</p>
      <h1 className="text-3xl font-semibold">This desk is locked</h1>
      <p className="text-ink-80">Your role can read the board. Admin actions stay with an admin account.</p>
      <Link href="/companies" className="text-accent">
        Back to the watchlist
      </Link>
    </div>
  );
}
