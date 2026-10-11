const ACCESS = "access_token";
const REFRESH = "refresh_token";

export function getAccessToken(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(ACCESS) || "";
}

export function setAccessToken(token: string) {
  window.localStorage.setItem(ACCESS, token);
}

export function getRefreshToken(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(REFRESH) || "";
}

export function setSession(access: string, refresh: string) {
  window.localStorage.setItem(ACCESS, access);
  window.localStorage.setItem(REFRESH, refresh);
}

export function clearAccessToken() {
  window.localStorage.removeItem(ACCESS);
  window.localStorage.removeItem(REFRESH);
}

export function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export function updatesSocketUrl(): string {
  const token = getAccessToken();
  const configured = process.env.NEXT_PUBLIC_WS_URL;
  const base = (configured || apiBase().replace(/^http/, "ws")).replace(/\/$/, "");
  return `${base}/ws/updates?token=${encodeURIComponent(token)}`;
}
