"use client";

import { useState } from "react";

import api from "@/api/apiclient/axios";
import type { ApiResponse } from "@/types/api";

type Queued = {
  id: number;
  kind: string;
  portal: string;
  status: string;
  already_running: boolean;
};

export function SyncButton({ onQueued, compact = false }: { onQueued?: () => void; compact?: boolean }) {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");

  async function sync() {
    setPending(true);
    setMessage("");
    try {
      const body = (await api.post("/api/admin/sync/")) as ApiResponse<Queued[]>;
      const fresh = body.data.filter((row) => !row.already_running);
      setMessage(
        fresh.length
          ? "Sync started. Prices and the floorsheet usually take a few minutes."
          : "A sync is already running.",
      );
      onQueued?.();
    } catch (err) {
      const text = err && typeof err === "object" && "message" in err ? String(err.message) : "Sync failed.";
      setMessage(text);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        className="min-h-10 rounded-lg bg-accent px-4 text-sm font-semibold text-[#081018] disabled:opacity-60"
        onClick={() => void sync()}
        disabled={pending}
      >
        {pending ? "Queuing…" : "Sync now"}
      </button>
      {message ? (
        <p className={`m-0 text-ink-80 ${compact ? "max-w-56 text-xs" : "text-sm"}`}>{message}</p>
      ) : null}
    </div>
  );
}
