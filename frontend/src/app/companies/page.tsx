"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import api from "@/api/apiclient/axios";
import { ErrorState } from "@/components/error/ErrorState";
import { PageHeader } from "@/components/layout/page-header";
import { getAccessToken } from "@/lib/session";
import { useMe } from "@/lib/use-me";
import type { ApiResponse } from "@/types/api";

type Card = {
  id: number;
  symbol: string;
  name: string;
  sector: string;
  active: boolean;
  last_close: string | null;
  prev_close: string | null;
};

export default function CompaniesPage() {
  const router = useRouter();
  const me = useMe();
  const [rows, setRows] = useState<Card[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    try {
      const body = (await api.get("/api/companies/")) as ApiResponse<Card[]>;
      setRows(body.data);
      setError("");
    } catch (err) {
      const status = err && typeof err === "object" && "status" in err ? Number(err.status) : 0;
      if (status === 403) {
        router.replace("/forbidden");
        return;
      }
      const message = err && typeof err === "object" && "message" in err ? String(err.message) : "Could not load the watchlist.";
      setError(message);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="grid gap-5">
      <PageHeader kicker="Watchlist" title="NEPSE board" description="Last close and the move from the prior session." />
      {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}
      {!rows.length && !error ? <p className="text-ink-60">Loading quotes…</p> : null}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {rows.map((row) => {
          const last = row.last_close == null ? null : Number(row.last_close);
          const prev = row.prev_close == null ? null : Number(row.prev_close);
          const change = last != null && prev != null ? last - prev : null;
          const up = change != null && change >= 0;
          return (
            <Link key={row.id} href={`/companies/${row.id}`} className="rounded-2xl border border-line bg-paper p-4 hover:border-accent">
              <div className="flex items-baseline justify-between">
                <span className="text-lg font-semibold">{row.symbol}</span>
                <span className={up ? "text-[var(--color-up)]" : "text-[var(--color-down)]"}>
                  {last == null ? "—" : last.toFixed(2)}
                </span>
              </div>
              <p className="mt-1 text-sm text-ink-60">{row.name}</p>
              <p className={`mt-3 text-sm ${up ? "text-[var(--color-up)]" : "text-[var(--color-down)]"}`}>
                {change == null ? "No change yet" : `${up ? "+" : ""}${change.toFixed(2)}`}
              </p>
              {me?.role === "admin" ? (
                <button
                  type="button"
                  className="mt-3 text-xs text-ink-60"
                  onClick={(event) => {
                    event.preventDefault();
                    void api.patch(`/api/companies/${row.id}/`, { active: false }).then(() => load());
                  }}
                >
                  Remove from watchlist
                </button>
              ) : null}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
