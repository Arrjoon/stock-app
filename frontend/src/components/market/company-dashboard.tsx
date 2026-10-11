"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import api from "@/api/apiclient/axios";
import { ErrorState } from "@/components/error/ErrorState";
import { PageHeader } from "@/components/layout/page-header";
import { PriceChart } from "@/components/market/price-chart";
import { getAccessToken } from "@/lib/session";
import { useLiveRefresh } from "@/lib/use-live";
import type { ApiResponse } from "@/types/api";

type Company = { id: number; symbol: string; name: string; sector: string };
type Price = { date: string; close: string; volume: number };
type Broker = { broker: string; net_qty: number; buy_qty: number; sell_qty: number };
type BehaviorPoint = {
  date: string;
  vwap: string;
  close_vs_vwap_pct: number;
  pressure: number;
  is_volume_anomaly: boolean;
  news_count: number;
  next_day_return_pct: number | null;
  next_day_volume_change_pct: number | null;
  top_buyers: Broker[];
  top_sellers: Broker[];
};
type Article = {
  id: number;
  title: string;
  portal: string;
  published_at: string | null;
  url: string;
  tags: { symbol: string; confidence: number }[];
};

async function loadPayload<T>(path: string): Promise<T> {
  const body = (await api.get(path)) as ApiResponse<T>;
  return body.data;
}

export function CompanyDashboard({ companyKey }: { companyKey: string }) {
  const router = useRouter();
  const [company, setCompany] = useState<Company | null>(null);
  const [prices, setPrices] = useState<Price[]>([]);
  const [latest, setLatest] = useState<BehaviorPoint | null>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    try {
      const profile = await loadPayload<Company>(`/api/companies/${companyKey}/`);
      const [series, behavior, news] = await Promise.all([
        loadPayload<Price[]>(`/api/companies/${profile.id}/prices/?range=30d`),
        loadPayload<{ latest: BehaviorPoint | null }>(`/api/companies/${profile.id}/behavior/?range=30d`),
        loadPayload<Article[]>(`/api/news/?company_id=${profile.id}`),
      ]);
      setCompany(profile);
      setPrices(series);
      setLatest(behavior.latest);
      setArticles(news);
      setError("");
    } catch (err) {
      const message = err && typeof err === "object" && "message" in err ? String(err.message) : "Could not load company.";
      setError(message);
    }
  }, [companyKey, router]);

  useEffect(() => {
    void load();
  }, [load]);

  const connected = useLiveRefresh(load);

  if (!company && !error) {
    return <p className="text-ink-60">Loading company…</p>;
  }

  return (
    <div className="grid gap-6">
      <PageHeader
        kicker={connected ? "Live" : "Connecting"}
        title={company ? `${company.symbol} · ${company.name}` : companyKey.toUpperCase()}
        description={company?.sector || "Prices, tagged news, and broker behavior refresh when new data lands."}
      />
      {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}
      <section className="rounded-2xl border border-line bg-paper p-4">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-60">Price and volume</h2>
        {prices.length ? <PriceChart points={prices} /> : <p className="text-ink-60">No prices in the last 30 days.</p>}
      </section>
      <section className="grid gap-3 md:grid-cols-3">
        <Metric label="Close vs VWAP" value={latest ? `${latest.close_vs_vwap_pct.toFixed(2)}%` : "—"} />
        <Metric label="Pressure" value={latest ? latest.pressure.toFixed(0) : "—"} />
        <Metric label="Volume anomaly" value={latest?.is_volume_anomaly ? "Yes" : "No"} />
      </section>
      <section className="grid gap-4 md:grid-cols-2">
        <BrokerList title="Top net buyers" rows={latest?.top_buyers || []} />
        <BrokerList title="Top net sellers" rows={latest?.top_sellers || []} />
      </section>
      {latest ? (
        <p className="text-sm text-ink-80">
          News that day: {latest.news_count}. Next session return:{" "}
          {latest.next_day_return_pct === null ? "n/a" : `${latest.next_day_return_pct.toFixed(2)}%`}. Next session
          volume change:{" "}
          {latest.next_day_volume_change_pct === null ? "n/a" : `${latest.next_day_volume_change_pct.toFixed(1)}%`}.
        </p>
      ) : null}
      <section className="grid gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-60">Categorized news</h2>
        {articles.length === 0 ? <p className="text-ink-60">No tagged articles for this company.</p> : null}
        {articles.map((article) => (
          <a key={article.id} href={article.url} className="rounded-xl border border-line bg-paper px-4 py-3 hover:border-accent">
            <p className="font-medium">{article.title}</p>
            <p className="text-sm text-ink-60">
              {article.portal}
              {article.published_at ? ` · ${article.published_at.slice(0, 10)}` : ""}
              {article.tags[0] ? ` · ${Math.round(article.tags[0].confidence * 100)}%` : ""}
            </p>
          </a>
        ))}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-paper p-4">
      <p className="text-xs uppercase tracking-wide text-ink-60">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function BrokerList({ title, rows }: { title: string; rows: Broker[] }) {
  return (
    <div className="rounded-2xl border border-line bg-paper p-4">
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink-60">{title}</h2>
      {rows.length === 0 ? <p className="text-ink-60">No floorsheet sample for the latest day.</p> : null}
      <ul className="grid gap-1 text-sm">
        {rows.slice(0, 5).map((row) => (
          <li key={row.broker} className="flex justify-between gap-3">
            <span>Broker {row.broker}</span>
            <span className="text-ink-80">net {row.net_qty}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
