"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import api from "@/api/apiclient/axios";
import { ErrorState } from "@/components/error/ErrorState";
import { PageHeader } from "@/components/layout/page-header";
import { PriceChart } from "@/components/market/price-chart";
import { useMe } from "@/lib/use-me";
import { apiBase, getAccessToken } from "@/lib/session";
import { useLiveRefresh } from "@/lib/use-live";
import type { ApiResponse } from "@/types/api";

type Company = { id: number; symbol: string; name: string; sector: string };
type Price = { date: string; close: string; volume: number; open: string; high: string; low: string };
type Broker = { broker: string; net_qty: number };
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
  tags: { symbol: string; confidence: number; source: string }[];
};

const RANGES = ["7d", "30d", "90d"];

async function loadPayload<T>(path: string): Promise<T> {
  const body = (await api.get(path)) as ApiResponse<T>;
  return body.data;
}

export function CompanyDashboard({ companyKey }: { companyKey: string }) {
  const router = useRouter();
  const me = useMe();
  const [range, setRange] = useState("30d");
  const [company, setCompany] = useState<Company | null>(null);
  const [prices, setPrices] = useState<Price[]>([]);
  const [points, setPoints] = useState<BehaviorPoint[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [watchlist, setWatchlist] = useState<Company[]>([]);
  const [tagDrafts, setTagDrafts] = useState<Record<number, string>>({});
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    try {
      const profile = await loadPayload<Company>(`/api/companies/${companyKey}/`);
      const [series, behavior, news, board] = await Promise.all([
        loadPayload<Price[]>(`/api/companies/${profile.id}/prices/?range=${range}`),
        loadPayload<{ latest: BehaviorPoint | null; points: BehaviorPoint[] }>(
          `/api/companies/${profile.id}/behavior/?range=${range}`,
        ),
        loadPayload<{ results: Article[] }>(`/api/news/?company_id=${profile.id}`),
        loadPayload<Company[]>("/api/companies/"),
      ]);
      const stories = news.results || [];
      setCompany(profile);
      setPrices(series);
      setPoints(behavior.points || []);
      setArticles(stories);
      setWatchlist(board);
      setTagDrafts((current) => {
        const next: Record<number, string> = {};
        for (const article of stories) {
          next[article.id] = current[article.id] ?? article.tags.map((tag) => tag.symbol).join(", ");
        }
        return next;
      });
      setError("");
    } catch (err) {
      const status = err && typeof err === "object" && "status" in err ? Number(err.status) : 0;
      if (status === 403) {
        router.replace("/forbidden");
        return;
      }
      const message = err && typeof err === "object" && "message" in err ? String(err.message) : "Could not load company.";
      setError(message);
    }
  }, [companyKey, range, router]);

  useEffect(() => {
    void load();
  }, [load]);

  const live = useLiveRefresh(load);
  const latest = points.at(-1) || null;
  const last = prices.at(-1);
  const prev = prices.at(-2);
  const change = last && prev ? Number(last.close) - Number(prev.close) : null;
  const chart = useMemo(() => {
    const byDate = new Map(points.map((point) => [point.date, point]));
    return prices.map((price) => {
      const point = byDate.get(price.date);
      return { ...price, vwap: point?.vwap ?? null, anomaly: Boolean(point?.is_volume_anomaly) };
    });
  }, [points, prices]);

  async function correctTags(articleId: number) {
    const typed = (tagDrafts[articleId] || "")
      .split(",")
      .map((part) => part.trim().toUpperCase())
      .filter(Boolean);
    const companyIds = typed.map((symbol) => watchlist.find((item) => item.symbol.toUpperCase() === symbol)?.id);
    if (typed.length !== companyIds.filter(Boolean).length) {
      setError(`Use symbols separated by commas: ${watchlist.map((item) => item.symbol).join(", ")}`);
      return;
    }
    await api.post(`/api/news/${articleId}/recategorize/`, { company_ids: companyIds });
    await load();
  }

  async function download(format: "csv" | "json") {
    if (!company) {
      return;
    }
    const response = await fetch(`${apiBase()}/api/companies/${company.id}/export/?format=${format}`, {
      headers: { Authorization: `Bearer ${getAccessToken()}` },
    });
    if (response.status === 403) {
      router.replace("/forbidden");
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${company.symbol}.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  }

  if (!company && !error) {
    return <p className="text-ink-60">Loading quote…</p>;
  }

  const up = change !== null && change >= 0;

  return (
    <div className="grid gap-5">
      <PageHeader
        kicker={live.connected ? "Live" : "Reconnecting"}
        title={company ? company.symbol : companyKey.toUpperCase()}
        description={company ? `${company.name} · ${company.sector || "NEPSE"}` : "Quote, volume, and tagged news."}
      />
      {live.notice ? <p className="rounded-lg bg-[var(--color-warn)] px-3 py-2 text-sm text-[#1a1408]">{live.notice}</p> : null}
      {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}
      <section className="grid gap-4 rounded-2xl border border-line bg-paper p-4 md:grid-cols-[1.2fr_1fr]">
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-60">Last close</p>
          <p className={`mt-1 text-4xl font-semibold ${up ? "text-[var(--color-up)]" : "text-[var(--color-down)]"}`}>
            {last ? Number(last.close).toFixed(2) : "—"}
          </p>
          <p className="mt-1 text-sm text-ink-80">
            {change === null ? "Waiting for a second session" : `${up ? "+" : ""}${change.toFixed(2)} vs prior close`}
          </p>
        </div>
        <div className="flex flex-wrap items-start justify-end gap-2">
          {RANGES.map((value) => (
            <button
              key={value}
              type="button"
              className={`rounded-full px-3 py-1 text-sm ${range === value ? "bg-accent-soft text-ink" : "text-ink-60"}`}
              onClick={() => setRange(value)}
            >
              {value}
            </button>
          ))}
          {me?.role === "admin" || me?.role === "analyst" ? (
            <>
              <button type="button" className="rounded-full border border-line px-3 py-1 text-sm" onClick={() => void download("csv")}>
                CSV
              </button>
              <button type="button" className="rounded-full border border-line px-3 py-1 text-sm" onClick={() => void download("json")}>
                JSON
              </button>
            </>
          ) : null}
        </div>
      </section>
      <section className="rounded-2xl border border-line bg-paper p-4">
        <div className="mb-2 flex gap-4 text-xs uppercase tracking-wide text-ink-60">
          <span className="text-[#5b9dff]">Close</span>
          <span className="text-[var(--color-warn)]">VWAP</span>
          <span className="text-[var(--color-down)]">Anomaly</span>
        </div>
        {chart.length ? <PriceChart points={chart} /> : <p className="text-ink-60">No prices in this window.</p>}
      </section>
      <section className="grid gap-3 md:grid-cols-3">
        <Metric label="Close vs VWAP" value={latest ? `${latest.close_vs_vwap_pct.toFixed(2)}%` : "—"} tone={latest && latest.close_vs_vwap_pct >= 0 ? "up" : "down"} />
        <Metric label="Pressure" value={latest ? latest.pressure.toFixed(0) : "—"} tone={latest && latest.pressure >= 0 ? "up" : "down"} />
        <Metric label="Volume anomaly" value={latest?.is_volume_anomaly ? "Flagged" : "Normal"} tone={latest?.is_volume_anomaly ? "down" : "up"} />
      </section>
      <section className="grid gap-4 md:grid-cols-2">
        <BrokerList title="Top net buyers" rows={latest?.top_buyers || []} />
        <BrokerList title="Top net sellers" rows={latest?.top_sellers || []} />
      </section>
      {latest ? (
        <p className="text-sm text-ink-80">
          News that day: {latest.news_count}. Next session return{" "}
          {latest.next_day_return_pct === null ? "n/a" : `${latest.next_day_return_pct.toFixed(2)}%`}. Volume change{" "}
          {latest.next_day_volume_change_pct === null ? "n/a" : `${latest.next_day_volume_change_pct.toFixed(1)}%`}.
        </p>
      ) : null}
      <section className="grid gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-60">Tape</h2>
        {articles.length === 0 ? <p className="text-ink-60">No tagged articles for this company.</p> : null}
        {articles.map((article) => (
          <article key={article.id} className="rounded-xl border border-line bg-paper px-4 py-3">
            <a href={article.url} className="font-medium hover:text-accent">
              {article.title}
            </a>
            <p className="mt-1 flex flex-wrap gap-2 text-sm text-ink-60">
              <span>{article.portal}</span>
              {article.published_at ? <span>{article.published_at.slice(0, 10)}</span> : null}
              {article.tags.map((tag) => (
                <span key={`${article.id}-${tag.symbol}`} className="rounded-full bg-white/5 px-2 py-0.5">
                  {tag.symbol} {Math.round(tag.confidence * 100)}% {tag.source}
                </span>
              ))}
            </p>
            {me?.role === "admin" || me?.role === "analyst" ? (
              <div className="mt-2 flex gap-2">
                <input
                  className="min-h-9 flex-1 rounded-lg border border-line bg-transparent px-2 text-sm"
                  aria-label={`Tags for ${article.title}`}
                  placeholder="NICA, NABIL"
                  value={tagDrafts[article.id] ?? ""}
                  onChange={(event) => setTagDrafts((current) => ({ ...current, [article.id]: event.target.value }))}
                />
                <button type="button" className="rounded-lg bg-accent px-3 text-sm font-semibold text-[#081018]" onClick={() => void correctTags(article.id)}>
                  Save tags
                </button>
              </div>
            ) : null}
          </article>
        ))}
      </section>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone: "up" | "down" }) {
  return (
    <div className="rounded-2xl border border-line bg-paper p-4">
      <p className="text-xs uppercase tracking-wide text-ink-60">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${tone === "up" ? "text-[var(--color-up)]" : "text-[var(--color-down)]"}`}>{value}</p>
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
