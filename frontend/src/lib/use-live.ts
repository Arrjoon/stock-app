"use client";

import { useEffect, useState } from "react";

import { updatesSocketUrl } from "@/lib/session";

export function useLiveRefresh(onUpdate: () => void) {
  const [connected, setConnected] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let socket: WebSocket | null = null;
    let closed = false;
    let attempt = 0;
    let timer: number | undefined;

    const poll = window.setInterval(() => onUpdate(), 30000);

    function open() {
      socket = new WebSocket(updatesSocketUrl());
      socket.onopen = () => {
        attempt = 0;
        setConnected(true);
      };
      socket.onclose = () => {
        setConnected(false);
        if (closed) {
          return;
        }
        const wait = Math.min(15000, 1000 * 2 ** attempt);
        attempt += 1;
        timer = window.setTimeout(open, wait);
      };
      socket.onmessage = (event) => {
        onUpdate();
        try {
          const body = JSON.parse(event.data) as { event?: string };
          if (body.event === "alert") {
            setNotice("New alert");
            window.setTimeout(() => setNotice(""), 4000);
          }
        } catch {
          /* ignore non-json frames */
        }
      };
    }

    open();
    return () => {
      closed = true;
      window.clearInterval(poll);
      if (timer) {
        window.clearTimeout(timer);
      }
      socket?.close();
    };
  }, [onUpdate]);

  return { connected, notice };
}
