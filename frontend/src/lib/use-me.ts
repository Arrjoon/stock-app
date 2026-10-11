"use client";

import { useEffect, useState } from "react";

import api from "@/api/apiclient/axios";
import { getAccessToken, SESSION_EVENT } from "@/lib/session";
import type { ApiResponse } from "@/types/api";

export type Me = {
  email: string;
  role: string;
};

export function useMe() {
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    let cancelled = false;

    function refresh() {
      if (!getAccessToken()) {
        setMe(null);
        return;
      }
      api
        .get("/api/auth/me/")
        .then((body) => {
          if (!cancelled) {
            setMe((body as unknown as ApiResponse<Me>).data);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setMe(null);
          }
        });
    }

    refresh();
    window.addEventListener(SESSION_EVENT, refresh);
    return () => {
      cancelled = true;
      window.removeEventListener(SESSION_EVENT, refresh);
    };
  }, []);

  return me;
}
