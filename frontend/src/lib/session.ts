const ACCESS = "access_token";

export function getAccessToken(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(ACCESS) || "";
}

export function setAccessToken(token: string) {
  window.localStorage.setItem(ACCESS, token);
}

export function clearAccessToken() {
  window.localStorage.removeItem(ACCESS);
}

export function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export function updatesSocketUrl(): string {
  const token = getAccessToken();
  const base = apiBase().replace(/^http/, "ws");
  return `${base}/ws/updates?token=${encodeURIComponent(token)}`;
}
