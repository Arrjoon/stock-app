"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import api from "@/api/apiclient/axios";
import { ErrorState } from "@/components/error/ErrorState";
import { PageHeader } from "@/components/layout/page-header";
import { getAccessToken } from "@/lib/session";
import { useLiveRefresh } from "@/lib/use-live";
import type { ApiResponse } from "@/types/api";

type Row = {
  id: number;
  symbol: string;
  name: string;
  volatility_pct: number;
  volume: number;
  news_count: number;
};

type ComparePayload = {
  range: string;
  most_volatile: Row[];
  most_active: Row[];
  most_in_the_news: Row[];
};

export function CompareDashboard() {
  const router = useRouter();
  const [payload, setPayload] = useState<ComparePayload | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    try {
      const body = (await api.get("/api/compare/?range=30d")) as ApiResponse<ComparePayload>;
      setPayload(body.data);
      setError("");
    } catch (err) {
      const message = err && typeof err === "object" && "message" in err ? String(err.message) : "Could not load comparison.";
      setError(message);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  const connected = useLiveRefresh(load);

  return (
    <div className="grid gap-6">
      <PageHeader
        kicker={connected ? "Live" : "Connecting"}
        title="Compare companies"
        description="Ranked over the last 30 days. Volatility is the standard deviation of daily returns. Activity is total volume. News is tagged articles."
      />
      {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}
      {!payload && !error ? <p className="text-ink-60">Loading comparison…</p> : null}
      {payload ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <RankList title="Most volatile" rows={payload.most_volatile} format={(row) => `${row.volatility_pct.toFixed(2)}%`} />
          <RankList title="Most active" rows={payload.most_active} format={(row) => row.volume.toLocaleString()} />
          <RankList title="Most in the news" rows={payload.most_in_the_news} format={(row) => String(row.news_count)} />
        </div>
      ) : null}
    </div>
  );
}

function RankList({
  title,
  rows,
  format,
}: {
  title: string;
  rows: Row[];
  format: (row: Row) => string;
}) {
  return (
    <section className="rounded-2xl border border-line bg-paper p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-60">{title}</h2>
      <ol className="grid gap-2">
        {rows.map((row, index) => (
          <li key={row.id}>
            <Link href={`/companies/${row.id}`} className="flex items-baseline justify-between gap-3 rounded-lg px-2 py-1.5 hover:bg-white/5">
              <span>
                <span className="mr-2 text-ink-60">{index + 1}</span>
                <span className="font-semibold">{row.symbol}</span>
                <span className="mt-0.5 block text-xs text-ink-60">{row.name}</span>
              </span>
              <span className="text-sm text-ink-80">{format(row)}</span>
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
