"use client";

import { useEffect, useState } from "react";

import { updatesSocketUrl } from "@/lib/session";

export function useLiveRefresh(onUpdate: () => void) {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socket = new WebSocket(updatesSocketUrl());
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = () => onUpdate();
    return () => socket.close();
  }, [onUpdate]);

  return connected;
}
