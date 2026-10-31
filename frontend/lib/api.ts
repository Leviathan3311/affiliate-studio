"use client";

import { useCallback, useEffect, useState } from "react";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN = "gp.token";
const WORKSPACE = "gp.workspace";

// shortcut: bearer token in localStorage; move to an httpOnly cookie behind a same-origin proxy
// before handling real customer data at scale.
export const session = {
  token: () => (typeof window === "undefined" ? null : localStorage.getItem(TOKEN)),
  workspace: () => (typeof window === "undefined" ? null : localStorage.getItem(WORKSPACE)),
  setToken: (t: string) => localStorage.setItem(TOKEN, t),
  setWorkspace: (id: string) => localStorage.setItem(WORKSPACE, id),
  clear: () => {
    localStorage.removeItem(TOKEN);
    localStorage.removeItem(WORKSPACE);
  },
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public fields: Record<string, string> = {},
  ) {
    super(message);
  }
}

type FastApiDetail = string | { loc: (string | number)[]; msg: string }[];

export async function api<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = session.token();
  const ws = session.workspace();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (ws) headers.set("X-Workspace-Id", ws);
  if (init.json !== undefined) headers.set("Content-Type", "application/json");

  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1${path}`, {
      ...init,
      headers,
      body: init.json !== undefined ? JSON.stringify(init.json) : init.body,
    });
  } catch {
    throw new ApiError(0, "Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.");
  }
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/auth/")) {
    session.clear();
    // Full reload on purpose: drops every cached screen state for the expired session.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = "/login";
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail: FastApiDetail | undefined = body?.detail;
    if (Array.isArray(detail)) {
      const fields = Object.fromEntries(
        detail.map((d) => [String(d.loc[d.loc.length - 1]), d.msg.replace(/^Value error, /, "")]),
      );
      throw new ApiError(res.status, "Vui lòng kiểm tra các trường được đánh dấu.", fields);
    }
    throw new ApiError(res.status, detail || `Lỗi ${res.status}`);
  }
  return body as T;
}

/** Minimal fetch-on-mount hook with optional polling. */
export function useApi<T>(path: string | null, pollMs?: number) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchInto = useCallback(
    (isLive: () => boolean = () => true) =>
      path
        ? api<T>(path).then(
            (d) => {
              if (!isLive()) return;
              setData(d);
              setError(null);
            },
            (e: ApiError) => isLive() && setError(e),
          )
        : Promise.resolve(),
    [path],
  );

  useEffect(() => {
    let live = true;
    const isLive = () => live; // ignore responses for a path we have left
    fetchInto(isLive);
    const id = pollMs
      ? setInterval(() => document.visibilityState === "visible" && fetchInto(isLive), pollMs)
      : undefined;
    return () => {
      live = false;
      clearInterval(id);
    };
  }, [fetchInto, pollMs]);

  const reload = useCallback(() => fetchInto(), [fetchInto]);

  return { data, error, loading: path !== null && data === null && error === null, reload, setData };
}

/** Current time, refreshed on an interval (render must stay pure). */
export function useNow(ms = 30000) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), ms);
    return () => clearInterval(id);
  }, [ms]);
  return now;
}
