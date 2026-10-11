"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import api from "@/api/apiclient/axios";
import { setSession } from "@/lib/session";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
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
    <form className="grid w-full max-w-sm gap-4" onSubmit={onSubmit}>
      <h1 className="m-0 text-center text-2xl font-semibold tracking-tight">Sign in</h1>
      <input
        className="min-h-11 rounded-lg border border-line bg-paper px-3 text-ink outline-none"
        type="email"
        placeholder="Email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        autoComplete="username"
        required
      />
      <input
        className="min-h-11 rounded-lg border border-line bg-paper px-3 text-ink outline-none"
        type="password"
        placeholder="Password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        autoComplete="current-password"
        required
      />
      {error ? <p className="m-0 text-center text-sm text-danger">{error}</p> : null}
      <button
        className="min-h-11 rounded-lg bg-accent font-semibold text-[#081018] disabled:opacity-60"
        type="submit"
        disabled={pending}
      >
        {pending ? "Signing in…" : "Login"}
      </button>
    </form>
  );
}
