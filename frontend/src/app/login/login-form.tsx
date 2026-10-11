"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import api from "@/api/apiclient/axios";
import { ErrorState } from "@/components/error/ErrorState";
import { setSession } from "@/lib/session";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("viewer@example.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const body = (await api.post("/api/auth/login/", { email, password })) as {
        access: string;
        refresh: string;
        role?: string;
      };
      setSession(body.access, body.refresh);
      router.push(body.role === "admin" ? "/admin" : "/companies");
    } catch (err) {
      const message = err && typeof err === "object" && "message" in err ? String(err.message) : "Login failed.";
      setError(message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="grid max-w-md gap-3 rounded-2xl border border-line bg-paper p-5" onSubmit={onSubmit}>
      <label className="grid gap-1 text-sm text-ink-80">
        Email
        <input
          className="min-h-10 rounded-lg border border-line bg-transparent px-3 text-ink"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
      </label>
      <label className="grid gap-1 text-sm text-ink-80">
        Password
        <input
          className="min-h-10 rounded-lg border border-line bg-transparent px-3 text-ink"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
      </label>
      {error ? <ErrorState message={error} /> : null}
      <button
        className="min-h-10 rounded-lg bg-accent px-4 font-semibold text-[#081018] disabled:opacity-60"
        type="submit"
        disabled={pending}
      >
        {pending ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
