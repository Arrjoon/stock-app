"use client";

import { useEffect, useState } from "react";

import api from "@/api/apiclient/axios";
import { getAccessToken } from "@/lib/session";
import type { ApiResponse } from "@/types/api";

export type Me = {
  email: string;
  role: string;
};

export function useMe() {
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    if (!getAccessToken()) {
      return;
    }
    let cancelled = false;
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
    return () => {
      cancelled = true;
    };
  }, []);

  return me;
}
