"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import api from "@/api/apiclient/axios";
import { ErrorState } from "@/components/error/ErrorState";
import { PageHeader } from "@/components/layout/page-header";
import { SyncButton } from "@/components/market/sync-button";
import { getAccessToken } from "@/lib/session";
import { useMe } from "@/lib/use-me";
import type { ApiResponse } from "@/types/api";

type Run = {
  id: number;
  kind: string;
  portal: string;
  status: string;
  items: number;
  error: string;
  started_at: string;
  finished_at: string | null;
};

type Account = { id: number; email: string; role: string; is_active: boolean };

export function AdminSync() {
  const router = useRouter();
  const me = useMe();
  const [runs, setRuns] = useState<Run[]>([]);
  const [users, setUsers] = useState<Account[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    try {
      const body = (await api.get("/api/admin/crawl-runs/")) as ApiResponse<Run[]>;
      setRuns(body.data);
      const people = (await api.get("/api/admin/users/")) as ApiResponse<Account[]>;
      setUsers(people.data);
      setError("");
    } catch (err) {
      const text = err && typeof err === "object" && "message" in err ? String(err.message) : "Could not load sync status.";
      setError(text);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  const active = runs.some((run) => run.status === "queued" || run.status === "running");

  useEffect(() => {
    if (!active) {
      return;
    }
    const timer = window.setInterval(() => void load(), 4000);
    return () => window.clearInterval(timer);
  }, [active, load]);

  return (
    <div className="grid gap-6">
      <PageHeader
        kicker="Admin"
        title="Sync market data"
        description="Sync now fetches news, a month of prices, and the latest floorsheet immediately. "
      />
      {me && me.role !== "admin" ? <ErrorState message="Only an admin can start a sync." /> : null}
      {me?.role === "admin" ? (
        <div className="flex flex-wrap gap-2">
          <SyncButton onQueued={() => void load()} />
          <button type="button" className="rounded-lg border border-line px-3 py-2 text-sm" onClick={() => void queue("prices", "nepse")}>
            Queue prices
          </button>
          <button type="button" className="rounded-lg border border-line px-3 py-2 text-sm" onClick={() => void queue("floorsheet", "nepse")}>
            Queue floorsheet
          </button>
          <button type="button" className="rounded-lg border border-line px-3 py-2 text-sm" onClick={() => void queue("news", "merolagani")}>
            Queue MeroLagani
          </button>
        </div>
      ) : null}
      {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}
      <section className="overflow-x-auto rounded-2xl border border-line bg-paper">
        <table className="w-full text-left text-sm">
          <thead className="text-ink-60">
            <tr>
              <th className="px-4 py-3 font-medium">Kind</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Items</th>
              <th className="px-4 py-3 font-medium">Started</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id} className={`border-t border-line ${run.status === "failed" ? "bg-danger-bg" : ""}`}>
                <td className="px-4 py-3">
                  {run.kind}
                  {run.portal ? <span className="text-ink-60"> · {run.portal}</span> : null}
                  {run.error ? <span className="mt-1 block text-xs text-danger">{run.error}</span> : null}
                </td>
                <td className="px-4 py-3">{run.status}</td>
                <td className="px-4 py-3">{run.items}</td>
                <td className="px-4 py-3 text-ink-80">{run.started_at.slice(0, 16).replace("T", " ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {runs.length === 0 && !error ? <p className="px-4 py-3 text-ink-60">No crawl runs yet.</p> : null}
      </section>
      {me?.role === "admin" ? (
        <section className="overflow-x-auto rounded-2xl border border-line bg-paper">
          <h2 className="px-4 pt-4 text-sm font-semibold uppercase tracking-wide text-ink-60">Users</h2>
          <table className="w-full text-left text-sm">
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-t border-line">
                  <td className="px-4 py-3">{user.email}</td>
                  <td className="px-4 py-3">
                    <select
                      className="bg-transparent"
                      value={user.role}
                      onChange={(event) => void patchUser(user.id, { role: event.target.value })}
                    >
                      <option value="admin">admin</option>
                      <option value="analyst">analyst</option>
                      <option value="viewer">viewer</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <button type="button" className="text-ink-80" onClick={() => void patchUser(user.id, { is_active: !user.is_active })}>
                      {user.is_active ? "Active" : "Inactive"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}
    </div>
  );

  async function queue(kind: string, portal: string) {
    await api.post("/api/admin/crawl-runs/", { kind, portal });
    await load();
  }

  async function patchUser(id: number, body: { role?: string; is_active?: boolean }) {
    await api.patch(`/api/admin/users/${id}/`, body);
    await load();
  }
}
